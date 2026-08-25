# Kitt kurulum paketi (WiX)

Bu klasör, Kitt'in Windows kurulum paketi (MSI) için WiX Toolset
kaynağını içerir. Tasarım gerekçesi için `KITT_ARCHITECTURE.md`
bölüm 10'a ("Installer Architecture") bakabilirsiniz.

## Dosyalar

- `wix/Package.wxs`: ürün kimliği (Name, Manufacturer, Version,
  UpgradeCode), yükseltme politikası (`MajorUpgrade`) ve kurulum
  dizini (`%SystemRoot%\System32\`, bkz. aşağıdaki "Neden System32"
  bölümü).
- `wix/Components.wxs`: kurulan içerik. `kittua.dll` ve
  `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Keyboard Layouts\`
  altındaki Windows klavye düzeni registry kaydı.
- `wix/Localization.wxl`: kurulum arayüzü için minimal İngilizce
  metinler.

## Derleme

MSI'ı derlemenin kanonik yolu, repo kökünden `tools/package.ps1`
çalıştırmaktır. Önce `kittua.dll`'i derler, sonra doğru `-D`
tanımlarıyla WiX'i çağırır:

```powershell
./tools/package.ps1
```

WiX'i doğrudan çağırmak isterseniz (örneğin bir `.wxs` değişikliğini
hata ayıklamak için), DLL yolunu ve ürün sürümünü preprocessor
değişkeni olarak vermeniz gerekir:

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
edilmesini gerektirir. Bu tek seferlik, kullanıcı bazlı bir karar,
bu repodaki script'ler tarafından sessizce otomatikleştirilmez.
`wix` komutu `WIX7015` hatası verirse, sözleşmeyi önce kendiniz kabul
edin (neyi kabul ettiğinizi görmek için https://wixtoolset.org/osmf/
adresine bakabilirsiniz):

```powershell
wix eula accept wix7
```

`tools/package.ps1` bunu kontrol eder, sözleşme henüz kabul
edilmemişse sizin adınıza kabul etmek yerine aynı talimatı ekrana
yazdırır.

`WixToolset.UI.wixext` eklentisi (`Package.wxs`'ten referans verilen
minimal kurulum arayüzü için gerekli), henüz önbelleğe alınmamışsa
`tools/package.ps1` tarafından otomatik olarak eklenir
(`wix extension add WixToolset.UI.wixext`).

## Bu kurulum paketi ne yapar

1. `kittua.dll`'i `%SystemRoot%\System32\` içine kopyalar (bkz.
   "Neden System32" bölümü). Bu uygulamalar için normal bir konum
   değil, ama Kitt bir uygulama değil; Windows'un yükleyeceği bir
   klavye düzeni DLL'i.
2. `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Keyboard Layouts\00010422`
   altına bir klavye düzeni kaydı yazar (`Layout File`, `Layout Text`,
   `Layout Id` değerleri, gerekçe için `wix/Components.wxs` içindeki
   yorumlara bakabilirsiniz). Bu key ismi bu makinenin gerçek
   registry'sine karşı doğrulandı: Microsoft'un kendi in-box
   konvansiyonuna göre bir dilin varsayılan olmayan düzeni
   `000N<LANGID>` şeklinde numaralanır, N artan bir sayaç
   (Ukraynaca'nın varsayılan düzeni `00000422`'de, "Enhanced"
   varyantı `00020422`'de duruyor), yani `00010422` hem boşta hem de
   Microsoft'un kendi numaralandırmasıyla tutarlı. Tahmini bir
   üçüncü taraf konvansiyonu değil.
3. Yükseltme davranışını (`MajorUpgrade`) kaydeder, böylece gelecekteki
   0.x.y sürümleri bu kurulumun yerine geçer, ayrı bir düzen olarak
   görünmez.

Hiçbir custom action, script ya da arka plan süreci çalıştırmaz.
Yukarıdakilerin tümü yalnızca native WiX/MSI ilkel öğeleriyle
(`Component`, `File`, `RegistryValue`) uygulanmıştır. `KITT_ARCHITECTURE.md`
bölüm 16'ya ("elle yazılmış yıkıcı registry script'leri yerine mümkün
olduğunda MSI/WiX ilkel öğelerini kullan") uygun olarak.

## Yönetici izinleri

Bu MSI'ı kurmak (ya da kaldırmak) `HKEY_LOCAL_MACHINE`'e ve
`%SystemRoot%\System32\`'e yazar, ikisi de Yönetici izni gerektirir.
MSI'ı çalıştırdığınızda Windows yükseltme (UAC) isteyecek, ya da
yükseltilmiş bir kabuktan `msiexec /i ...` çalıştırabilirsiniz.

MSI'ı derlemek (`tools/package.ps1` / `wix build`) Yönetici izni
gerektirmez, yalnızca diskte dosya derler.

## Neden System32

Bir Windows klavye düzeni DLL'i normal bir uygulama gibi
`%ProgramFiles%` altına kurulamaz. Bu gerçek bir makinede test
edilerek doğrulandı: `%ProgramFiles%\Kitt\` altına kurulan bir Kitt
Windows Ayarlar'ın dil/klavye listesinde görünüyordu (registry kaydı
doğru okunuyordu) ama görev çubuğunun gerçek klavye değiştirme
menüsünde hiç çıkmıyordu, Win+Space ile ona geçilemiyordu. Yani
kayıtlı görünse de Windows onu gerçekten aktive etmiyordu.

`kittua.dll`'i doğrudan `%SystemRoot%\System32\` içine kurunca sorun
düzeldi. Microsoft'un kendi klavye düzeni DLL'leri de (`KBDUS.DLL`,
`KBDUR.DLL`, `KBDTUQ.DLL` gibi) hep System32'nin kendisinde durur,
bir alt klasörde değil. Kitt bu konvansiyonu takip ediyor.

## Gerçek makineye kurma

Kitt gerçek bir Windows makinesinde uçtan uca test edildi: kurulum,
harfler, rakamlar, noktalama, yön tuşları ve AltGr çalıştığı
doğrulandı. Yine de klavye düzeni kurmak sistem geneli, makine bazlı
bir değişiklik (`HKEY_LOCAL_MACHINE`, Windows giriş düzeni sistemi),
bu yüzden geliştirirken bir değişiklik denemek isterseniz atılabilir
bir test VM'i kullanmanız daha güvenli olur.

Önerilen akış:

1. MSI'ı `tools/package.ps1` ile derleyin (yükseltme gerektirmez).
2. Üretilen `dist/kitt-0.1.0-x64.msi`'yi kurun (`msiexec /i kitt-0.1.0-x64.msi`,
   yükseltilmiş olarak) ve `KITT_ARCHITECTURE.md` bölüm 12.6'daki
   ("Installation Tests") elle yapılan kontrol listesini uygulayın.
3. Sorun yaşarsanız `msiexec /x kitt-0.1.0-x64.msi`'nin temiz şekilde
   kaldırdığını doğrulayın.

## Checksum doğrulama

`tools/package.ps1`, `dist/` altında `.msi` dosyasının yanına bir
`.sha256` dosyası yazar (`KITT_ARCHITECTURE.md` bölüm 11: "SHA-256
checksum'ları oluşturulur"). Şununla doğrulayın:

```powershell
Get-FileHash dist/kitt-0.1.0-x64.msi -Algorithm SHA256
```

Çıktıyı ilgili `.sha256` dosyasının içeriğiyle karşılaştırın.
