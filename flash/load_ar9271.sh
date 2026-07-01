#!/system/bin/sh
# NetHunter AR9271 loader - Realme C51 (RMX3830) - CORRECT dependency order.
# Run as root:  su -c "sh /sdcard/nethunter_modules/load_ar9271.sh"
set -e
M=/sdcard/nethunter_modules
FW=/vendor/firmware/ath9k_htc

echo "[*] Installing AR9271 firmware..."
mount -o remount,rw /vendor 2>/dev/null || true
mkdir -p "$FW"
cp "$M/htc_9271-1.4.0.fw" "$FW/" && echo "    firmware installed"

echo "[*] Clean previous attempts..."
rmmod ath9k_htc 2>/dev/null || true
rmmod ath9k_common 2>/dev/null || true
rmmod ath9k_hw 2>/dev/null || true
rmmod ath 2>/dev/null || true
rmmod mac80211 2>/dev/null || true

echo "[*] Loading modules (cfg80211 = stock, already loaded)..."
# If stock cfg80211 is NOT present, uncomment the next line:
# insmod "$M/cfg80211.ko" && echo "    cfg80211 (ours)"
insmod "$M/mac80211.ko"     && echo "    mac80211"
insmod "$M/ath.ko"          && echo "    ath (ath_common)"
insmod "$M/ath9k_hw.ko"     && echo "    ath9k_hw"
insmod "$M/ath9k_common.ko" && echo "    ath9k_common"
insmod "$M/ath9k_htc.ko"    && echo "    ath9k_htc"

echo "[*] Loaded ath modules:"; lsmod | grep -i -E "ath|mac80211" || true
echo "[*] Recent ath9k dmesg:"; dmesg | grep -i -E "ath9k|usb|wlan" | tail -n 20 || true
echo "[*] Now plug in the AR9271 OTG adapter, then run: ip link"
