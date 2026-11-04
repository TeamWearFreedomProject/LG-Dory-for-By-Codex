# LG G Watch (dory) postmarketOS port

This repository is the workspace for experiments on the original LG G Watch
(dory). The device flashing and on-device measurements happen on the user's
computer; the cloud workspace can prepare packages and images but has no USB
connection to the watch.

## Confirmed baseline

The postmarketOS `pmaports` device package `device-lg-dory` and kernel package
`linux-lg-dory` exist in the archived GitLab.com mirror at commit
`817ed870e92a64963d926354fb74c75090811fcc` (2024-11-03). Check the current
upstream before basing a build on these older files:
<https://gitlab.postmarketos.org/postmarketOS/pmaports>.

The archived device package describes a 280 × 280 armhf watch, uses fastboot
boot images, and declares `HAS_WLAN = false`. Its Linux 3.10.40 config has
`CONFIG_FB_MSM_MDSS=y` and `CONFIG_DRM` disabled. It has an Android USB gadget,
but `CONFIG_USB_ETH` and Bluetooth `CONFIG_BT_BNEP` are disabled. The package
depends on `msm-fb-refresher` and has an AsteroidOS subpackage. These facts
describe the archived *build configuration*, not what is currently booting on
the user's watch.

## Development order

1. Fetch the current `pmbootstrap` and `pmaports` from the official GitLab host.
   Keep them outside this checkout or use a documented local overlay. Record the
   exact revisions used for each image.
2. Build the existing dory image and a boot image, then verify its generated
   artifacts and build logs in the cloud. The user handles fastboot on their
   local computer. Prefer a temporary boot for first hardware checks if that
   bootloader supports it.
3. Establish a network link that the user's computer supports without a driver
   installation. Test the link, IP addresses, and SSH login before removing
   reliance on ADB. USB Ethernet gadget is a candidate, but the
   gadget function and host USB class must match the host OS. Bluetooth PAN is
   another candidate only if the Bluetooth controller and BNEP can be enabled.
4. Bring up the existing display and touch stack with a compositor or X server.
   User applications need no direct framebuffer drawing. The archived kernel
   exposes framebuffer rather than DRM, so compositor backend compatibility
   must be verified before choosing Wayland/XWayland packages. XWayland running
   in another demonstration does not by itself prove this kernel supports it.
5. Record device results (boot log, input events, display behavior, USB IDs,
   network interfaces) and adjust device/kernel packages in small, testable
   steps.

The user's watch currently runs AsteroidOS normally. Its host is Windows
10/11 without administrator privileges, so installing a USB driver is
unavailable. **The existing shell is ADB, not a COM port.** On the watch,
`uname -r` reports 3.10.40, `/sys/class/net` lists only `ifb0`, `ifb1`, `lo`,
and `sit0`, and the Android USB gadget reports `ffs`. The watch has `/usr/sbin/sshd`
and `/usr/bin/nc`. Windows shows no USB network adapter for the watch.

### First SSH path: ADB port forwarding

ADB can forward a PC loopback port to port 22 on the watch without changing the
Windows driver or the watch's USB gadget. The installed `/usr/sbin/sshd` has no
`sshd.service` on this AsteroidOS installation, and neither `ss` nor `netstat`
is available. Check the daemon configuration and host keys before starting it:

```sh
adb shell '/usr/sbin/sshd -t 2>&1; echo sshd_check:$?'
adb shell 'ls -l /etc/ssh/ssh_host_*_key 2>/dev/null'
```

On the user's running watch, `sshd -t` exits with code 0 and an ECDSA host key
exists at `/etc/ssh/ssh_host_ecdsa_key`. No `sshd` process was running at the
time of the check. `adb shell '/usr/sbin/sshd'` can start
the daemon directly. Confirm it remains running with `adb shell 'ps | grep [s]shd'`.
From the directory containing `adb.exe` on Windows:

```powershell
.\adb.exe forward tcp:2222 tcp:22
ssh -o HostKeyAlias=lg-dory-adb -p 2222 root@127.0.0.1
.\adb.exe forward --remove tcp:2222
```

Alternatively run `scripts/ssh-over-adb.ps1` with `-Adb` set to the full path
of `adb.exe`; it removes the forward when SSH exits. The helper itself has not
been run on Windows yet. This gives an SSH shell and
file transfer over the existing USB connection; ADB remains the transport.
**Verified on the user's Windows PC:** starting `sshd`, forwarding port 2222,
and running the SSH command reached a `root@dory` shell. The host key was
recorded under `lg-dory-adb`; Windows reported the same key was previously
known for `192.168.2.15`.
This forwarding path depends on AsteroidOS's `adbd`; a postmarketOS image must
provide its own tested access path before replacing the working installation.

### postmarketOS over Flint2

The user reports that a postmarketOS image built by an earlier ChatGPT-assisted
GitHub Actions workflow from a 2022 base exposes USB RNDIS to a Flint2 OpenWRT
router, and SSH from Flint2 works. A newer base did not boot. Windows identifies
the 2022 image's USB device as an ADB Recovery Interface. The exact build
revision is not yet recorded. Flint2 is unavailable when the user is away from
home, so it cannot be the primary access path. If the Windows PC can SSH to
Flint2 and Flint2
can SSH to the watch, Windows OpenSSH can reach the watch through the router:

```powershell
ssh -J root@<flint2-lan-address> root@<watch-rndis-address>
```

This uses the existing OpenWRT USB networking and requires no Windows USB
driver change. Verify the two SSH legs separately before using the jump. The
Windows driver binding can be investigated later using the watch's USB
descriptors and Windows hardware IDs; the OpenWRT result establishes that the
postmarketOS gadget can provide a network link to a Linux host.

The archived 2024 `postmarketos-initramfs` code programs Android USB RNDIS with
default USB ID `18d1:d001` unless `deviceinfo_usb_idVendor` and
`deviceinfo_usb_idProduct` override it. Its comment identifies that default as
Google/Nexus 4 fastboot. The archived dory deviceinfo has no override. This is
a plausible reason Windows binds an ADB/Recovery driver to the gadget; it is
not confirmed for the user's 2022 image. Obtain that image's USB VID/PID and
interface hardware IDs, then test a device-side descriptor change with a
separate build before relying on Windows automatic RNDIS/NCM matching. Keep
the working 2022 image available while testing.

When that image is booted on Windows, its binding can be inspected without
administrator privileges using Device Manager → ADB Recovery Interface →
Properties → Details → Hardware Ids and Compatible Ids. Capture those IDs and
the exact Windows version; they distinguish an ID collision from a function
descriptor problem.

The [rebuild workflow](../.github/workflows/legacy-dory-2022.yml) now pins
`pmaports` to `e07103fb745821390a7640460f091f842d9e08ae` and
`pmbootstrap` to `9d93d34b65363ec6bb32b6345ec9ed685e5f9602`. It retains
ARMHF/GCC 6 and enables SSH. `0x4EE3` is a USB product-ID experiment, not a
confirmed Windows fix. No postmarketOS image has been built or flashed in this
cloud session yet.
