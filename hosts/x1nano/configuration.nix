{ config, pkgs, ... }:

{
  imports = [
    ../../profiles/full/configuration.nix
    ./hardware-configuration.nix
  ];

  networking.hostName = "x1nano";

  # Fingerprint authentication (not provided by nixos-hardware)
  services.fprintd.enable = true;
  security.pam.services.login.fprintAuth = true;
  security.pam.services.sudo.fprintAuth = true;

  # Firmware updates via LVFS (BIOS / Thunderbolt)
  # 使い方: fwupdmgr refresh && fwupdmgr update
  services.fwupd.enable = true;

  # NOTE: TLP / fstrim / Intel microcode / Intel GPU stack / TrackPoint は
  # nixos-hardware (lenovo-thinkpad-x1-nano) 経由で有効化済み.
  # thermald は ThinkPad の DTT (thinkpad_acpi/dytc_lapmode) と競合し
  # 自動的に exit するため入れない (ベンダ側 EC が thermal を管理).
}
