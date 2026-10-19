#
# Copyright (C) 2023 The LineageOS Project
#
# SPDX-License-Identifier: Apache-2.0
#

# Namespace
MIUICAMERA_PATH := vendor/xiaomi/camera
CAMERA_PACKAGE_NAME := com.android.camera

# Properties
TARGET_SYSTEM_PROP += $(MIUICAMERA_PATH)/system.prop

# SEPolicy
BOARD_VENDOR_SEPOLICY_DIRS += $(MIUICAMERA_PATH)/sepolicy/vendor
SYSTEM_PRIVATE_SEPOLICY_DIRS += $(MIUICAMERA_PATH)/sepolicy/private
SYSTEM_PUBLIC_SEPOLICY_DIRS += $(MIUICAMERA_PATH)/sepolicy/public
