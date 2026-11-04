# LG G Watch (dory) postmarketOS experiments

The [2022 ARMHF build workflow](.github/workflows/legacy-dory-2022.yml) uses
pinned postmarketOS sources from December 2022. It applies a narrow
apk 3 output compatibility fixes to pmbootstrap while retaining its
package-signature, version, and command exit checks. It keeps the original dory
Linux 3.10/GCC 6 port and builds a minimal image with SSH enabled. GitHub
Actions uploads compressed `boot.img` and `lg-dory.img` plus logs and checksums.
The build checks the Android boot header and the watch's 22 MiB boot limit.
These checks do not establish that the image boots on hardware.

Run **LG G Watch 2022 ARMHF image** from GitHub Actions after the workflow is
available on the repository's default branch. The `usb_product_id` input
selects `0xD001` for the historical default or `0x4EE3` as an experimental
Windows recognition candidate. The latter may still need USB descriptor changes;
Windows recognition has not been verified. Keep the known working image while
testing. The temporary image login password is `ci-test-only`; change it after
first boot.

See [porting notes](docs/porting-plan.md) for the confirmed AsteroidOS SSH path,
the Windows USB issue, and the next device measurements.
