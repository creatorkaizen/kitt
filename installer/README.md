# Kitt kurulum paketi (WiX)

Bu klasör, Kitt'in Windows kurulum paketi (MSI) için WiX Toolset
kaynağını içerir. Tasarım gerekçesi için `KITT_ARCHITECTURE.md`
bölüm 10'a ("Installer Architecture") ve bölüm 35'e ("Microsoft/
Windows Implementation Notes") bakabilirsin.

## Dosyalar

- `wix/Package.wxs` — ürün kimliği (Name, Manufacturer, Version,
  UpgradeCode), yükseltme politikası (`MajorUpgrade`) ve kurulum
  dizini (`%ProgramFiles%\Kitt\`).
- `wix/Components.wxs` — kurulan içerik: `kittua.dll` ve
  `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Keyboard Layouts\`
  altındaki Windows klavye-düzeni registry kaydı.
- `wix/Localization.wxl` — kurulum arayüzü için minimal İngilizce
  metinler.

## Derleme

MSI'ı derlemenin kanonik yolu, repo kökünden `tools/package.ps1`
çalıştırmaktır — önce `kittua.dll`'i derler, sonra doğru `-D`
tanımlarıyla WiX'i çağırır:

```powershell
./tools/package.ps1
```

WiX'i doğrudan çağırmak istersen (örn. bir `.wxs` değişikliğini
hata ayıklamak için), DLL yolunu ve ürün sürümünü preprocessor
değişkeni olarak vermen gerekir:

```powershell
$env:Path += ";C:\Program Files\dotnet;$env:USERPROFILE\.dotnet\tools"
wix build `
  installer/wix/Package.wxs `
  installer/wix/Components.wxs `
  -loc installer/wix/Localization.wxl `
  -ext WixToolset.UI.wixext `
  -arch x64 `
  -d KittuaDllPath="build/windows/src/windows/Release/kittua.dll" `
  -out dist/kitt-0.1.0-x64.msi
```

### WiX Toolset v7 EULA

WiX Toolset v7, herhangi bir komutu (build dahil) çalıştırmadan önce
Open Source Maintenance Fee (OSMF) lisans sözleşmesinin kabul
edilmesini gerektirir. Bu, tek seferlik, kullanıcı bazlı bir karardır
— bu repodaki script'ler tarafından sessizce otomatikleştirilmez.
`wix` komutu `WIX7015` hatası verirse, sözleşmeyi önce kendin kabul
et (neyi kabul ettiğini görmek için https://wixtoolset.org/osmf/
adresine bakabilirsin):

```powershell
wix eula accept wix7
```

`tools/package.ps1` bunu kontrol eder ve sözleşme henüz kabul
edilmemişse, senin adına kabul etmek yerine aynı talimatı ekrana
yazdırır.

`WixToolset.UI.wixext` eklentisi (`Package.wxs`'ten referans verilen
minimal kurulum arayüzü için gerekli), henüz önbelleğe alınmamışsa
`tools/package.ps1` tarafından otomatik olarak eklenir (`wix
extension add WixToolset.UI.wixext`).

## Bu kurulum paketi ne yapar

1. `kittua.dll`'i `%ProgramFiles%\Kitt\` altına kopyalar.
2. `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Keyboard Layouts\00010422`
   altına bir klavye-düzeni kaydı yazar (`Layout File`, `Layout Text`,
   `Layout Id` değerleri — gerekçe için `wix/Components.wxs`
   içindeki yorumlara bakabilirsin). Bu key ismi, bu makinenin
   gerçek registry'sine karşı doğrulandı: Microsoft'un kendi
   in-box konvansiyonuna göre bir dilin varsayılan-olmayan düzeni
   `000N<LANGID>` şeklinde numaralanır, N artan bir sayaçtır
   (Ukraynaca'nın varsayılan düzeni `00000422`'de, "Enhanced"
   varyantı `00020422`'de duruyor), yani `00010422` hem boşta hem de
   Microsoft'un kendi numaralandırmasıyla tutarlı — tahmini bir
   üçüncü-taraf konvansiyonu değil.
3. Yükseltme davranışını (`MajorUpgrade`) kaydeder, böylece
   gelecekteki 0.x.y sürümleri bu kurulumun yerine geçer, ayrı/
   ilgisiz bir düzen olarak görünmez.

Hiçbir custom action, script ya da arka plan süreci çalıştırmaz.
Yukarıdakilerin tümü yalnızca native WiX/MSI ilkel öğeleriyle
(`Component`, `File`, `RegistryValue`) uygulanmıştır,
`KITT_ARCHITECTURE.md` bölüm 16'ya ("elle yazılmış yıkıcı registry
script'leri yerine mümkün olduğunda MSI/WiX ilkel öğelerini kullan")
uygun olarak.

## Yönetici izinleri

Bu MSI'ı kurmak (ya da kaldırmak) `HKEY_LOCAL_MACHINE`'e ve
`%ProgramFiles%`'a yazar, ikisi de Yönetici izni gerektirir. MSI'ı
çalıştırdığında Windows yükseltme (UAC) isteyecektir, ya da
yükseltilmiş bir kabuktan `msiexec /i ...` çalıştırabilirsin.

MSI'ı **derlemek** (`tools/package.ps1` / `wix build`) Yönetici izni
**gerektirmez** — yalnızca diskte dosya derler.

## ÖNEMLİ — geliştirme makinene kurma

**Bu MSI'ı yalnızca atılabilir bir test VM'inde kur/dene, asla ana
geliştirme makinende değil.** Bu, `KITT_ARCHITECTURE.md` bölüm
10'daki "Development installation" tavsiyesiyle uyumludur: gerçek
klavye-düzeni kurulumu sistem geneli, makine bazlı duruma dokunur
(`HKEY_LOCAL_MACHINE`, Windows giriş-düzeni sistemi). Geliştirme
için güvendiğin bir makineye kurmak, temizlenmesi zor
yanlış/sahipsiz bir klavye-düzeni kaydı bırakma ya da çalışırken
kendi klavye girişini bozma riski taşır — bu, registry key
isimlendirmesine ne kadar güvendiğinden bağımsızdır, çünkü henüz
gerçekten kurulmuş+seçilebilir bir Windows giriş düzeni olarak
uçtan uca test edilmedi.

Önerilen akış:

1. MSI'ı geliştirme makinende `tools/package.ps1` ile derle (yükseltme
   gerektirmez).
2. Üretilen `dist/kitt-0.1.0-x64.msi`'yi atılabilir bir Windows VM'ine
   kopyala (önce anlık görüntü/snapshot al).
3. Orada kur (`msiexec /i kitt-0.1.0-x64.msi`, yükseltilmiş olarak) ve
   `KITT_ARCHITECTURE.md` bölüm 12.6'daki ("Installation Tests") elle
   yapılan kontrol listesini uygula.
4. İşin bitince VM anlık görüntüsünü sil/geri al, ya da
   `msiexec /x kitt-0.1.0-x64.msi`'nin temiz şekilde kaldırdığını
   doğrula.

## Checksum doğrulama

`tools/package.ps1`, `dist/` altında `.msi` dosyasının yanına bir
`.sha256` dosyası yazar (`KITT_ARCHITECTURE.md` bölüm 11: "SHA-256
checksum'ları oluşturulur"). Şununla doğrula:

```powershell
Get-FileHash dist/kitt-0.1.0-x64.msi -Algorithm SHA256
```

ve çıktıyı ilgili `.sha256` dosyasının içeriğiyle karşılaştır.
