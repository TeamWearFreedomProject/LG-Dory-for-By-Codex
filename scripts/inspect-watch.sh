#!/bin/sh
# Read-only inventory to run in the existing AsteroidOS ADB shell on dory.
set -u
section() { printf '\n== %s ==\n' "$1"; }
section system
uname -a
section network_interfaces
ls -1 /sys/class/net 2>/dev/null || true
section usb_gadget
ls -1 /sys/class/udc 2>/dev/null || true
ls -1 /sys/class/android_usb 2>/dev/null || true
for usb_functions_file in /sys/class/android_usb/android0/functions /sys/kernel/config/usb_gadget/*/configs/*/functions/*; do
    if [ -f "$usb_functions_file" ]; then
        printf '%s: ' "$usb_functions_file"
        cat "$usb_functions_file"
    fi
done
section serial_ports
ls -1 /dev/ttyGS* /dev/ttyACM* 2>/dev/null || true
section display
ls -1 /dev/fb* /dev/dri/* 2>/dev/null || true
section relevant_kernel_config
if [ -r /proc/config.gz ]; then
    zcat /proc/config.gz 2>/dev/null | grep -E '^(CONFIG_USB_(ETH|G_NCM|G_ANDROID|F_RNDIS|CONFIGFS)|CONFIG_BT_BNEP|CONFIG_DRM|CONFIG_FB_MSM|CONFIG_WLAN)=' || true
elif [ -r "/boot/config-$(uname -r)" ]; then
    grep -E '^(CONFIG_USB_(ETH|G_NCM|G_ANDROID|F_RNDIS|CONFIGFS)|CONFIG_BT_BNEP|CONFIG_DRM|CONFIG_FB_MSM|CONFIG_WLAN)=' "/boot/config-$(uname -r)" || true
else
    printf 'kernel config not available\n'
fi
section ssh_server
for command_name in dropbear sshd nc socat stty; do
    command -v "$command_name" 2>/dev/null || true
done
