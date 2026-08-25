# Değişiklik Günlüğü

Bu projedeki tüm önemli değişiklikler bu dosyada belgelenir.

Format [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) esas
alınarak hazırlandı. Bu proje [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
kullanır (Kitt'e özgü sürümleme politikası için `KITT_ARCHITECTURE.md`
bölüm 14'e bakabilirsin).

## [Yayınlanmamış]

Şu ana kadarki çalışma, `KITT_ARCHITECTURE.md` bölüm 27'deki
("Suggested Milestones") M0 ile M3 arası kilometre taşlarına
karşılık geliyor. Henüz etiketlenmiş bir sürüm yayınlanmadı.

### Eklenenler

- **Klavye düzeni (M0):** Türkçe Q fiziksel klavye pozisyonlarına
  eşlenen, iyotlu sesli harfler (я/ю/є/ї) için `Y` tuşunda ölü tuş
  kullanan kanonik Ukraynaca mnemonik düzen
  (`layout/kitt.uk-UA.yaml`).
- **Üretici (M0):** `kittgen` Python paketi (parser, doğrulama,
  Unicode kontrolleri, Windows tablo üretimi, Markdown döküman
  üretimi, CLI). `python -m kittgen validate` ve
  `python -m kittgen generate` komutlarıyla çalışır. 66 gerekli
  Ukraynaca harfin tamamının erişilebilir olduğu doğrulandı.
- **Native katman (M1, sonra tamamen yeniden yazıldı):** `kittgen`,
  YAML klavye düzeninden bir Windows `KBDTABLES` C kaynak dosyası
  üretir (`src/windows/kitt_tables.c`). İlk sürüm sadece Ukraynaca
  harfleri elle seçip tabloya ekliyordu, gerçek makinede test
  edilince rakamlar, boşluk, yön tuşları, AltGr gibi tuşların
  sessizce çalışmadığı görüldü. Bunun üzerine generator, gerçek
  Windows Türkçe Q sürücüsünün (`KBDTUQ.DLL`) tüm tablosunu referans
  alacak şekilde yeniden yazıldı: her şey bu referanstan kopyalanıyor,
  sadece Kitt'in eşlediği yaklaşık 29 tuşun base/shift çıktısı
  değiştiriliyor. AltGr, Ctrl+Alt, sayısal tuş takımı, yön tuşları ve
  Türkçe aksan tuşları artık standart Türkçe Q'daki gibi çalışıyor.
- **Native derleme (M2):** `kittua.dll`'i üreten CMake build sistemi
  (`CMakeLists.txt`, `src/windows/CMakeLists.txt`, `kitt.def`,
  `resources.rc`), kanonik yerel derleme giriş noktası olan
  `tools/build.ps1` (YAML'dan native kaynağı yeniden üretir, sonra
  CMake/MSVC ile derler) ve `tools/clean.ps1`.
- **Kurulum paketi (M3):** WiX Toolset kaynağı
  (`installer/wix/Package.wxs`, `Components.wxs`, `Localization.wxl`)
  ve `tools/package.ps1`, SHA-256 checksum dosyasıyla birlikte
  `dist/kitt-<versiyon>-x64.msi` üretir. `kittua.dll`'i
  `%SystemRoot%\System32\` içine kurar (ilk sürüm `%ProgramFiles%`
  kullanıyordu, gerçek makinede test edilince Windows'un klavye
  düzenini orada aktive etmediği görüldü) ve klavye düzenini
  `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Keyboard Layouts\00010422`
  altına, yalnızca native WiX/MSI ilkel öğeleriyle kaydeder.
- **Testler:** birim, klavye düzeni ve snapshot testlerini kapsayan
  pytest test paketi (259 test), tam Ukraynaca alfabe erişilebilirliği
  ve deterministik üretim kapsamı dahil.
- **CI/CD:** GitHub Actions `ci.yml` (lint-and-test,
  build-windows-x64, package-windows-x64) ve `release.yml` (`v*`
  etiketiyle tetiklenen build, paketleme ve GitHub Release yayınlama;
  `layout.version` ile sürüm tutarlılığı kontrolü dahil).
- **Dokümantasyon:** kullanıcıya dönük `README.md`, üretilen eşleme
  referansı (`docs/mapping.md`).
- **Lisans:** MIT.

### Düzeltilenler

- CMake kurulum kuralları `ARCHIVE DESTINATION` içermiyordu, bu da
  `kittua.lib`'in kurulan ağaçtan sessizce düşmesine yol açıyordu.
  `kitt.def` de iki bağımsız yerde referans alınıyordu, bu ikisinin
  sessizce birbirinden ayrışması mümkündü.
- Kurulum paketi `%ProgramFiles%\Kitt\` yerine `%SystemRoot%\System32\`
  hedefleyecek şekilde düzeltildi (gerçek makinede test edilerek
  bulundu).
- Native tablo üretici, sadece elle seçilmiş tuşları değil, gerçek
  Türkçe Q klavyenin tüm tuş davranışını kapsayacak şekilde yeniden
  yazıldı.
