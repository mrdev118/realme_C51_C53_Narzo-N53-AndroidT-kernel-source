# AR9271 on Realme RMX3830 — final working backup

This folder is the recovery and reproducibility backup for the verified-safe run99 Atheros AR9271 driver stack.

## Final verified result

- Phone: Realme C51 `RMX3830`, Android 15
- Kernel: `5.15.178-android13-8-ge7eb24fc4398-ab236`
- Adapter: Atheros AR9271, USB ID `0cf3:9271`
- Firmware: `ath9k_htc/htc_9271-1.4.0.fw`, version 1.4
- Interfaces: `wlan1` managed and `wlan1mon` monitor
- Monitor mode: PASS, channel 1, 30 dBm reported
- Stock Wi-Fi: remained connected on `wlan0`
- Controlled USB unbind/rebind: PASS
- Real physical hub unplug: PASS, no reboot or panic
- SELinux after testing: `Enforcing`
- Magisk package: `artifacts/ar9271-rmx3830-magisk-run99.zip`

## Canonical GitHub build

- Repository: <https://github.com/mrdev118/realme_C51_C53_Narzo-N53-AndroidT-kernel-source>
- Run 99: <https://github.com/mrdev118/realme_C51_C53_Narzo-N53-AndroidT-kernel-source/actions/runs/29571282836>
- Commit: `7e14ce24d85a5166fbb9a353b1fd5b75e3220549`
- Artifact ID: `8403241506`
- GitHub artifact SHA-256: `bc350eb362c0d47df51cc6781fac10258e12aa4205276eafa6d0e2816782ac0d`

## Folder map

- `artifacts/` — run99 GitHub artifact and final Magisk ZIP
- `run99/` — extracted modules and ABI/layout verification output
- `FINAL_WALKTHROUGH.md` — root causes, fixes, validation, and future procedure
- `PHONE_COMMANDS.md` — normal usage and diagnostic commands
- `TEST_RESULTS.md` — final proof and identifiers
- `pstore_disconnect_panic/` — preserved run88 failure evidence
- Older run88 documents/artifacts are historical and unsafe; do not install run88

## Important rule

Install only the package whose module version is `run99-realme-kabi-1`. Run88 attached successfully but panicked on physical disconnect because its guessed ABI layout was wrong.



---

# Final run99 walkthrough and technical record

## Goal and constraints

The goal was to add Atheros AR9271 USB Wi-Fi support to a rooted Realme C51/RMX3830 without replacing the stock kernel. Builds stayed on GitHub Actions to avoid using local disk space. Only downloaded artifacts, test evidence, and recovery backups were kept locally.

## Why the earlier builds kept failing

There were three separate failure classes, so a build that compiled was not necessarily safe:

1. Early modules did not match the stock kernel's full LTO/CFI settings and could fail CFI at module load.
2. Run88 used guessed public-kernel structure layouts. It attached, loaded firmware, and made monitor mode work, but physical USB disconnect called `rfkill_pause_polling` through a bad `wiphy`/rfkill layout and panicked the kernel.
3. After exact wireless layouts were fixed, run97 still failed interface registration. Its `struct net_device.ieee80211_ptr` was at offset 768, while the stock Realme kernel expected 760.

## Exact root cause and final source fix

The stock Realme kernel preserves Android KABI differently from public AOSP. In `struct net_device`, Realme stores `l3mdev_ops` in Android KABI reserve slot 8 at offset 2544. Public AOSP placed `l3mdev_ops` inline at offset 536. That shifted later fields, including `ieee80211_ptr`, by eight bytes.

The run99 workflow patches `include/linux/netdevice.h` so the inline `CONFIG_NET_L3_MASTER_DEV` member is removed and reserve slot 8 is consumed with:

```c
ANDROID_KABI_USE(8, const struct l3mdev_ops *l3mdev_ops);
```

The workflow then compares generated layouts against stock BTF/layout evidence. Run99 passed all common `net_device` member offsets: size 2560, 138 common members, zero mismatches. It also passed the `wiphy`, `wireless_dev`, `cfg80211_ops`, `ieee80211_channel`, and `ieee80211_supported_band` layout gates.

## Canonical build

- GitHub Actions run: 99
- Run ID: `29571282836`
- Commit: `7e14ce24d85a5166fbb9a353b1fd5b75e3220549`
- Artifact ID: `8403241506`
- Artifact digest: `bc350eb362c0d47df51cc6781fac10258e12aa4205276eafa6d0e2816782ac0d`
- Vermagic matches the stock `5.15.178-android13-8` ab516 family

## Live validation sequence

1. Staged and hash-checked all five run99 modules.
2. Controlled-unbound the old driver and unloaded it without a reboot.
3. Loaded `mac80211`, `ath`, `ath9k_hw`, `ath9k_common`, and `ath9k_htc` from run99.
4. Rebound the connected AR9271; firmware 1.4 loaded and `wlan1` appeared.
5. Created `wlan1mon`, brought it UP, and verified monitor type, channel 1, and 30 dBm.
6. Performed a controlled sysfs unbind/rebind. Both passed and SELinux was restored to Enforcing.
7. Physically unplugged the complete hub/OTG lead from the phone while the AR9271 remained in the hub.
8. The phone stayed online with unchanged uptime. Dmesg ended with `ath9k_htc: USB layer deinitialized`; there was no panic or restart.

## Persistent installation

The final Magisk module is `ar9271_rmx3830`, version `run99-realme-kabi-1`. Its service waits for stock `cfg80211`, then loads the five modules in dependency order. Firmware is overlaid at `/vendor/firmware/ath9k_htc/htc_9271-1.4.0.fw`. The `ar9271-monitor` helper dynamically discovers the correct PHY from `wlan1`.

The enabled module was then tested through a complete Android reboot with the hub absent. Android finished boot, the service automatically loaded all five exact-hash modules, SELinux remained Enforcing, and no AR9271 warning or panic occurred. After wireless ADB was restored and the hub was connected, USB `0cf3:9271` bound automatically, firmware 1.4 loaded, and `wlan1` appeared. The installed helper created `wlan1mon` on the dynamically detected PHY, verified monitor mode/channel 1/30 dBm, then removed it cleanly. Stock `wlan0` stayed connected throughout.

## Future rebuild path

1. Start from the repository and the run99 workflow/source commit.
2. Preserve the exact full-LTO/CFI and MODVERSIONS configuration.
3. Preserve all ABI/layout gates; never accept compilation alone as proof.
4. Compare the generated structures against the phone's stock evidence.
5. Test in this order: module load, firmware, managed interface, monitor interface, controlled unbind/rebind, then real physical unplug.
6. Keep the hub unplugged during boot/recovery until the module stack is confirmed.

Run88 and its panic evidence remain in this backup only to prevent repeating the same ABI mistake.



---

# Final verified test results — run99

## Build identity

- Run ID: `29571282836`
- Commit: `7e14ce24d85a5166fbb9a353b1fd5b75e3220549`
- Artifact ID: `8403241506`
- Artifact SHA-256: `bc350eb362c0d47df51cc6781fac10258e12aa4205276eafa6d0e2816782ac0d`

## Module SHA-256 values

```text
b44483f28cdbdeb526c4cad3e533fe6c9f6fbf7abedda36ad1bc78f1a42aa861  ath.ko
01e4ec8d8604853eec0776a3c70d4fe1724ce69cfd1a94e7118cf6d8d61186e2  ath9k_common.ko
b519326ac478d0379989cf2994f17cefff5708d4b47c1bd6cc466e3ecb0ad596  ath9k_htc.ko
9b23ba2da756ac25a8e9123d140f3a8bf2142f358f9aacc7496ea55c72185850  ath9k_hw.ko
7934e0485815f3332349318b10d591125712a339bd13729ec98fcf08f738d673  mac80211.ko
78f7d592a95b419a02fde7440f30c606fc31a871cf0ce150ced40d4857173eb0  htc_9271-1.4.0.fw
```

## Results

- Exact config and full LTO/CFI: PASS
- Wireless structure ABI gates: PASS
- `net_device` size/member offsets: PASS, 2560 bytes and 138/138 common offsets
- Load all five modules: PASS
- Firmware version 1.4: PASS
- `wlan1` managed interface: PASS
- `wlan1mon` monitor interface: PASS
- Stock `wlan0` remains connected: PASS
- Controlled USB unbind: PASS
- Controlled USB rebind: PASS
- Physical hub unplug: PASS, phone remained alive
- Reboot persistence with hub absent: PASS
- Automatic bind after post-reboot hub connection: PASS
- Installed monitor helper after reboot: PASS
- SELinux returned to Enforcing: PASS

Final assessment: run99 is the first build verified for both operation and safe USB teardown on this phone.



---

# Phone commands for final run99

The Magisk module automatically loads the five modules at boot. Do not manually load run88 files.

## Check the driver

From the PC:

```text
adb shell "su -c 'cat /data/adb/modules/ar9271_rmx3830/module.prop; cat /data/local/tmp/ar9271-rmx3830.log; grep -E \"^(ath9k_htc|ath9k_common|ath9k_hw|ath|mac80211) \" /proc/modules'"
```

## Start monitor mode

In Termux on the phone:

```text
su -c ar9271-monitor start
```

Check status:

```text
su -c ar9271-monitor status
```

Stop and remove the monitor interface:

```text
su -c ar9271-monitor stop
```

The helper dynamically finds the PHY belonging to `wlan1`; it does not assume a fixed `phy1` number.

## Safe physical order

1. Keep the AR9271 plugged into the powered USB hub.
2. Plug the hub's USB-C/OTG lead into the phone.
3. Wait for `wlan1` to appear.
4. Stop monitor mode before disconnecting when convenient.
5. Unplug the hub's USB-C/OTG lead from the phone. Run99 has passed this real unplug test without a panic.

## Recovery disable

If a future experiment causes trouble, boot without the hub and run:

```text
adb shell "su -c 'touch /data/adb/modules/ar9271_rmx3830/disable; reboot'"
```

