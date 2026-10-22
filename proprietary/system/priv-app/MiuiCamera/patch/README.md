# MiuiCamera ultra-wide watermark fix

## Symptom

Taking an ultra-wide photo with the CV watermark enabled makes
`com.android.camera` crash in the `camera-saver` thread. A small preview JPEG
may still appear in DCIM, but the final JPEG is not written.

The log is:

```
FATAL EXCEPTION: camera-saver-8
java.lang.NullPointerException: Attempt to invoke virtual method
'int com.xiaomi.protocol.ICustomCaptureResult.getSequenceId()' on a null object reference
    at com.xiaomi.protocol.ICustomCaptureResult.toTotalCaptureResult(...)
    at com.android.camera2.compat.theme.custom.cv.cvwatermark.CvWatermarkUtil.processWatermark(...)
    at com.android.camera.storage.ParallelSaveRequest.save(...)
```

The ultra-wide capture path does not attach an `ICustomCaptureResult` to
`ParallelTaskData`. `CvWatermarkUtil.processWatermark()` passed that null value
straight into `ICustomCaptureResult.toTotalCaptureResult()`, which dereferences
it. Disabling the watermark avoids the call, which is why ultra-wide without a
watermark saves normally.

## Fix

`CvWatermarkUtil.processWatermark()` now returns early when either the custom
capture result or the converted `TotalCaptureResult` is null. The original JPEG
is then saved without a watermark instead of crashing the saver thread. This
matches the existing no-watermark behavior for shots where the camera metadata
is unavailable.

The smali change is:

```diff
@@ -1098,12 +1098,16 @@
 
     move-result-object v4
 
+    if-eqz v4, :cond_cv_watermark_skip
+
     const/4 v9, 0x0
 
     invoke-static {v4, v9}, Lcom/xiaomi/protocol/ICustomCaptureResult;->toTotalCaptureResult(Lcom/xiaomi/protocol/ICustomCaptureResult;I)Landroid/hardware/camera2/TotalCaptureResult;
 
     move-result-object v4
 
+    if-eqz v4, :cond_cv_watermark_skip
+
     const-wide/16 v5, 0x0
 
     cmp-long v5, v2, v5
@@ -2286,6 +2290,7 @@
 
     invoke-static {v9, v0, v1}, Lcom/android/camera/log/Log;->w(Ljava/lang/String;Ljava/lang/String;[Ljava/lang/Object;)V
 
+    :cond_cv_watermark_skip
     return-void
 .end method
```

## Build integration

`proprietary/system/priv-app/MiuiCamera/patch/classes4.dex` is the reassembled,
patched dex. The `MiuiCamera_patched_apk` genrule in `Android.bp` copies the
original prebuilt APK, replaces `classes4.dex`, and strips the old signature.
The existing `android_app_import` then signs the result with the platform key,
so the app still has its normal privileged permissions.

Build just the app with:

```sh
source build/envsetup.sh
breakfast surya userdebug
m MiuiCamera
```

A full `m bacon` rebuild and flash is needed to update the system image.

## Regenerating the patched dex

The patch was produced from the unmodified APK's `classes4.dex`:

```sh
unzip -p MiuiCamera.apk classes4.dex > classes4.dex
baksmali d classes4.dex -o classes4-smali
# apply the diff above to
# classes4-smali/com/android/camera2/compat/theme/custom/cv/cvwatermark/CvWatermarkUtil.smali
smali a classes4-smali -o classes4.dex
cp classes4.dex proprietary/system/priv-app/MiuiCamera/patch/classes4.dex
```
