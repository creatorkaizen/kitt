# Değişiklik Günlüğü

Bu projedeki tüm önemli değişiklikler bu dosyada belgelenir.

Format [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) esas
alınarak hazırlanmıştır, bu proje [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
kullanır (Kitt'e özgü sürümleme politikası için `KITT_ARCHITECTURE.md`
bölüm 14'e bakabilirsin).

## [Yayınlanmamış]

Şu ana kadarki çalışma, `KITT_ARCHITECTURE.md` bölüm 27'deki
("Suggested Milestones") M0–M3 kilometre taşlarına karşılık gelir.
Henüz etiketlenmiş (tagged) bir sürüm yayınlanmadı.

### Eklenenler

- **Klavye düzeni (M0):** Türkçe Q fiziksel klavye pozisyonlarına
  eşlenen, iyotlu sesli harfler (я/ю/є/ї) için `Y` tuşunda ölü tuş
  (dead key) kullanan kanonik Ukraynaca mnemonik düzen
  (`layout/kitt.uk-UA.yaml`).
- **Üretici (M0):** `kittgen` Python paketi (parser, doğrulama,
  Unicode kontrolleri, Windows tablo üretimi, Markdown döküman
  üretimi, CLI) — `python -m kittgen validate` ve
  `python -m kittgen generate` komutlarıyla. 66 gerekli Ukraynaca
  harfin tamamının erişilebilir olduğu doğrulandı.
- **Native katman (M1):** `kittgen`, YAML klavye düzeninden bir
  Windows `KBDTABLES` C kaynak dosyası üretir
  (`src/windows/kitt_tables.c`) — `VK_TO_WCHARS2`, ölü tuş/`DEADTRANS`,
  scan-code tablosu ve `KbdLayerDescriptor` export'u dahil, WDK
  klavye-düzeni DLL sözleşmesine uygun şekilde. Türkçe Q'ya özgü
  `VK_OEM_*` atamaları ve scan code'lar, gerçek Windows'un kendi
  Türkçe Q sürücüsüne (`KBDTUQ.DLL`) karşı doğrulandı.
- **Native derleme (M2):** `kittua.dll`'i üreten CMake build sistemi
  (`CMakeLists.txt`, `src/windows/CMakeLists.txt`, `kitt.def`,
  `resources.rc`), ayrıca kanonik yerel derleme giriş noktası olan
  `tools/build.ps1` (YAML'dan native kaynağı yeniden üretir, sonra
  CMake/MSVC ile derler) ve `tools/clean.ps1`.
- **Kurulum paketi (M3):** WiX Toolset kaynağı
  (`installer/wix/Package.wxs`, `Components.wxs`, `Localization.wxl`)
  ve `tools/package.ps1`, SHA-256 checksum dosyasıyla birlikte
  `dist/kitt-<versiyon>-x64.msi` üretir. `kittua.dll`'i kurar ve
  klavye düzenini
  `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Keyboard Layouts\00010422`
  altına, yalnızca native WiX/MSI ilkel öğeleri (custom action
  kullanmadan) ile kaydeder.
- **Testler:** birim, klavye düzeni/sözleşme ve snapshot testlerini
  kapsayan pytest test paketi (bu yazı itibarıyla 246 test) — tam
  Ukraynaca alfabe erişilebilirliği ve deterministik üretim
  kapsamı dahil.
- **CI/CD:** GitHub Actions `ci.yml` (lint-and-test,
  build-windows-x64, package-windows-x64 — `KITT_ARCHITECTURE.md`
  bölüm 13'e uygun) ve `release.yml` (`v*` etiketiyle tetiklenen
  build, paketleme ve GitHub Release yayınlama; `layout.version` ile
  sürüm tutarlılığı kontrolü dahil, bölüm 14'e uygun).
- **Dokümantasyon:** kullanıcıya dönük `README.md`; üretilen eşleme
  referansı (`docs/mapping.md`).

### Düzeltilenler

- CMake kurulum kuralları `ARCHIVE DESTINATION` içermiyordu, bu da
  `kittua.lib`'in kurulan/paketlenen ağaçtan sessizce düşmesine yol
  açıyordu; ayrıca `kitt.def` iki bağımsız yerde referans alınıyordu,
  bu da sessizce birbirinden ayrışabilirdi. Her ikisi de M2
  incelemesi sırasında düzeltildi.
