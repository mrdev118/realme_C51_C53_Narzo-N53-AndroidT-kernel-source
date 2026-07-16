# Complete AR9271 / RMX3830 walkthrough

## 1. Why the stock phone could not use AR9271

The phone's stock Wi-Fi stack contains `cfg80211` and the Unisoc `sprd_wlan_combo` driver, but not `mac80211` or the Atheros `ath9k_htc` family. AR9271 therefore enumerated over USB but had no usable driver stack.

Relevant stock configuration:

```text
CONFIG_MODULES=y
CONFIG_MODVERSIONS=y
CONFIG_CFG80211=m
CONFIG_MAC80211 is not set
CONFIG_CFI_CLANG=y
CONFIG_CFI_CLANG_SHADOW=y
CONFIG_LTO_CLANG_FULL=y
CONFIG_SHADOW_CALL_STACK=y
CONFIG_CLANG_VERSION=140007
```

## 2. Exact source and toolchain alignment

The working build uses:

- AOSP common kernel tag `android13-5.15.178_r00`
- Clang 14.0.7
- Full Clang LTO
- Clang CFI with shadow
- Shadow call stack
- Stock RMX3830 symbol CRC data from `Module.symvers`
- External-module builds for `net/mac80211` and `drivers/net/wireless/ath`

The external-module approach is essential: an in-tree full-LTO `make modules` attempted to link all of `vmlinux.o` and repeatedly exhausted the hosted runner/time budget. Building only the two external module trees completed in minutes.

## 3. Failure history and what each failure taught us

### Wrong `module_layout` CRC

Early modules were rejected because their `CONFIG_MODVERSIONS` CRC for `module_layout` did not match stock. The verified stock CRC is:

```text
module_layout=0x0222dd63
```

Every run-88 module contains this exact CRC.

### Wrong cfg80211/mac80211 API generation

An unpinned Android 5.15 branch expected newer `wiphy_work_*` helpers absent from the phone's stock `cfg80211`. Pinning exactly `android13-5.15.178_r00` removed that API mismatch.

### Kernel panic from missing CFI/LTO

The first CRC-patched `mac80211` load rebooted the phone. Pstore proved the cause:

```text
Kernel panic - not syncing: CFI failure
target: trace_event_raw_init
trace_module_notify
load_module
```

The previous module had been built with `CONFIG_LTO_NONE` and without stock CFI. Run 88 matches the phone's full-LTO/CFI settings, and the same `mac80211` load then completed with return code 0 without a reboot.

### GitHub full-LTO timeout

Runs 82 and 83 reached `LTO vmlinux.o` and were terminated. The workflow was changed to `modules_prepare` plus external module trees, avoiding a full kernel link.

### External modpost input errors

Android 5.15 `Module.symvers` requires five tab-separated fields, including an empty namespace field. Subsequent short failures exposed and fixed:

- four-field symbol rows;
- accidentally overwriting the corrected table;
- supplying the stock symbol table twice;
- a YAML comment splitting a backslash-continued shell command.

Run 88 passed all build, verification, firmware, packaging, and artifact-upload steps.

## 4. Successful build outputs

Required load order:

1. stock `cfg80211.ko` â€” already loaded by Android
2. `mac80211.ko`
3. `ath.ko`
4. `ath9k_hw.ko`
5. `ath9k_common.ko`
6. `ath9k_htc.ko`

Firmware path requested by the driver:

```text
ath9k_htc/htc_9271-1.4.0.fw
```

## 5. Exact physical connection sequence

For a controlled live test:

1. Keep the phone connected to the PC by USB cable.
2. Put the phone and PC on the same Wi-Fi network.
3. Load the modules and enable ADB TCP port 5555.
4. Confirm Wi-Fi ADB works before removing the cable.
5. Plug AR9271 into the hub port previously proven stable.
6. Connect separate hub power, if the hub supports it.
7. Do not connect the hub to the PC.
8. Unplug the USB cable from the phone only.
9. Plug the hub's USB-C/OTG host connector into the phone.

The unstable hub port previously produced USB error `-71`. The moved/stable port enumerated AR9271 as `1-1.1`.

## 6. Successful live test evidence

USB enumeration:

```text
1-1 214b:7260 USB2.0 HUB
1-1.1 0cf3:9271 UB91
```

Firmware and driver:

```text
ath9k_htc: Transferred FW: ath9k_htc/htc_9271-1.4.0.fw, size: 51008
ath9k_htc: HTC initialized with 33 credits
ath9k_htc: FW Version: 1.4
ieee80211 phy1: Atheros AR9271 Rev:1
```

Monitor mode:

```text
Interface wlan1mon
    type monitor
    wiphy 1
    channel 1 (2412 MHz), width: 20 MHz
    txpower 30.00 dBm
```

## 7. Firmware and SELinux

Loading firmware directly from `/data/local/tmp` while SELinux was Enforcing failed with `-13` because the kernel domain could not search `shell_data_file` directories. For the one-time live test, SELinux was switched to Permissive only during USB reauthorization and restored to Enforcing immediately after firmware transfer.

The Magisk package instead overlays firmware at:

```text
/vendor/firmware/ath9k_htc/htc_9271-1.4.0.fw
```

That avoids using `/data/local/tmp` as the normal persistent firmware location.

## 8. PRoot Kali note

PRoot's apparent root user normally does not have real Android kernel capabilities such as `CAP_NET_ADMIN`. Create or remove monitor interfaces using real Magisk `su` outside the PRoot boundary:

```sh
su -c ar9271-monitor start
su -c ar9271-monitor status
su -c ar9271-monitor stop
```

After `wlan1mon` exists, Kali tools can target it. If a Kali tool still reports raw-socket permission errors, start that operation from a real-root Termux/Android context rather than relying on PRoot's fake root.

## 9. Disconnect panic discovered after the successful monitor test

The adapter worked while attached, but unplugging the hub triggered:

```text
Unable to handle kernel paging request at virtual address 0x20020
pc: rfkill_pause_polling+0x18/0x50
lr: ath9k_htc_disconnect_device+0x54/0x17c [ath9k_htc]
ath9k_hif_usb_disconnect
usb_unbind_interface
usb_disconnect
Kernel panic - not syncing: Oops: Fatal exception
```

Register `x0` was `0x20000`, showing that `rfkill_pause_polling` received a bogus pointer. The likely cause is a conditional structure-layout mismatch in public cfg80211/mac80211 headersâ€”especially `struct wiphy`â€”because run 88 matched security flags and symbol CRCs but did not use the phone's complete `/proc/config.gz`.

The GitHub repository's published vendor tree is kernel 5.4.210, while this updated phone runs 5.15.178. That 5.4 source cannot define the current phone's exact wireless ABI. The safe next build must use the phone's complete 5.15 config and compare BTF/DWARF layouts before loading.

After the panic was diagnosed:

- `/data/adb/modules/ar9271_rmx3830/disable` was created;
- `ath9k_htc`, `ath9k_common`, `ath9k_hw`, `ath`, and `mac80211` were unloaded safely with no adapter attached;
- stock `cfg80211` and `sprd_wlan_combo` remained;
- full pstore files were copied into `pstore_disconnect_panic/`.

## 10. What is persistent and what is temporary

- Run-88 modules and live monitor mode: verified.
- Backup artifact and Magisk ZIP: created.
- Magisk boot loading: verified, but disabled because disconnect is unsafe.
- Current run-88 Magisk ZIP: forensic backup only; do not install.
- Safe persistence: not achieved until a new full-config build passes attach, monitor, and disconnect tests.

