# AR9271 disconnect crash â€” run 88

## Summary

The run-88 modules operate correctly while AR9271 remains attached, including monitor mode. Removing the OTG hub invokes the hot-unplug teardown path and crashes the kernel.

## Exact signature

```text
usb 1-1: USB disconnect
usb 1-1.1: USB disconnect
Unable to handle kernel paging request at virtual address 0000000000020020
pc : rfkill_pause_polling+0x18/0x50
lr : ath9k_htc_disconnect_device+0x54/0x17c [ath9k_htc]
x0 : 0000000000020000
ath9k_hif_usb_disconnect+0x74/0xb8 [ath9k_htc]
usb_unbind_interface+0x14c/0x4c0
usb_disconnect+0x160/0x598
Kernel panic - not syncing: Oops: Fatal exception
```

## Interpretation

`rfkill_pause_polling()` received pointer `0x20000`, which is invalid. `ath9k_htc_disconnect_device()` reaches this through teardown of the mac80211/cfg80211 device. The most likely cause is a public structure-layout mismatch produced by conditional kernel configuration fields. Symbol CRC equality and CFI compatibility do not prove structure layout equality.

The Realme GitHub source root reports kernel 5.4.210 and therefore does not match the phone's current 5.15.178 kernel. Run 88 used pinned AOSP 5.15.178 plus selected configuration fragments, not the complete live `/proc/config.gz`.

## Mandatory next-build gates

1. Use the complete phone `/proc/config.gz` as the configuration baseline.
2. Enable only the missing mac80211/ath9k modules on top of that baseline.
3. Preserve Clang 14.0.7, full LTO, CFI shadow, shadow call stack, and stock modversions.
4. Compare stock cfg80211 BTF layout with the build's headers for `struct wiphy` and related cfg80211 types.
5. Test in order: load with no adapter, attach, firmware, managed interface, monitor interface, controlled software detach, then physical detach.
6. Do not install persistently until every teardown test passes without pstore output.

## Current mitigation

The Magisk module is disabled and all custom modules are unloaded. Keep AR9271 disconnected.

