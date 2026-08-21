# Kitt

**Kitt**, Türkçe Q fiziksel klavyesi için tasarlanmış, Windows için native bir
Ukraynaca mnemonik klavye düzenidir. Basılan tuşun Latin/Türkçe harfinin sesi
Ukraynaca harfe nasıl benziyorsa, o mantıkla Ukraynaca yazmanı sağlar — ayrı
bir Ukraynaca fiziksel klavyeye, ekran klavyesi uygulamasına ya da arka
planda çalışan bir programa gerek kalmadan.

Kitt, diğer Windows klavye düzenleri gibi kurulur. Kurulduktan sonra normal
Windows dil/giriş değiştiricisinde diğer düzenlerinin yanında görünür.
Görev çubuğunda simgesi olan bir arka plan uygulaması yoktur; yazmadığın
sürece hiçbir şey çalışmaz.

## Kitt ne değildir

- klavye yeniden eşleme (remapping) uygulaması değildir;
- arka planda çalışan bir süreç ya da global klavye kancası (hook) değildir;
- bulut servisi değildir, internet bağlantısı gerektirmez;
- ekran/sanal klavye değildir.

Kitt, küçük bir native Windows klavye-düzeni DLL'i ve standart bir MSI
kurulum paketinden ibarettir. Tam teknik tasarım için
[`KITT_ARCHITECTURE.md`](KITT_ARCHITECTURE.md) dosyasına bakabilirsin.

## Desteklenen Windows sürümleri

- Windows 10 (x64)
- Windows 11 (x64)

x86/ARM64 henüz derlenmiyor; bkz. `KITT_ARCHITECTURE.md` bölüm 23.

## Kurulum

1. Projenin [Releases](../../releases) sayfasından en güncel
   `kitt-<versiyon>-x64.msi` dosyasını, eşleşen `.sha256` checksum dosyasıyla
   birlikte indir.
2. (Önerilir) Kurmadan önce checksum'ı doğrula:

   ```powershell
   Get-FileHash kitt-<versiyon>-x64.msi -Algorithm SHA256
   ```

   Çıktıyı `.sha256` dosyasının içeriğiyle karşılaştır.
3. MSI'ı çalıştır. Windows Yönetici izni (UAC) isteyecektir — bu beklenen bir
   durumdur. Bir klavye düzeni kurmak `HKEY_LOCAL_MACHINE` ve
   `%ProgramFiles%` altına yazma gerektirir, ikisi de sistem geneli,
   yönetici-yetkisi gerektiren konumlardır.
4. Kurulumdan sonra Kitt'i Windows'un normal giriş ayarlarından ekle:
   **Ayarlar → Saat ve Dil → Dil ve bölge → Klavye ekle**
   (ya da zaten eklenmiş düzenler arasında geçiş yapmak için
   **Windows tuşu + Boşluk** — ilk defa eklemek için aşağıya bak).

Son kullanıcı makinesinde Python, .NET ya da başka bir çalışma zamanına
ihtiyaç yoktur — Kitt derlenmiş native bir DLL olarak dağıtılır.

## Kullanım

Kitt bir giriş yöntemi olarak eklendikten sonra, diğer Windows klavye
düzenleri arasında geçiş yaptığın gibi geçiş yaparsın:

- **Win + Boşluk** — etkin giriş düzenleri arasında sırayla geçiş yapar.
- Ya da görev çubuğundaki dil/düzen göstergesine tıklayıp **Kitt**'i seç.

Yazarken normal bir alfabetik düzen gibi davranır:

- `Shift + tuş` büyük harf Ukraynaca karakteri üretir.
- `Caps Lock` harfleri beklendiği gibi etkiler.
- Tanıdık QWERTY noktalaması mümkün olduğunca korunur.
- Ukraynaca iyotlu sesli harfler (`я`, `ю`, `є`, `ї`), `Y` tuşuna basıp
  ardından ilgili sesli harfe basarak yazılır (`Y` tek başına `й` üretir) —
  bu, Ukraynacada gerçekten nasıl telaffuz edildiklerini yansıtır.

Tam, tuş tuş üretilen eşleme referansı için
[`docs/mapping.md`](docs/mapping.md) dosyasına bakabilirsin.

## Kaldırma

Kitt'i diğer Windows programları gibi kaldırabilirsin:
**Ayarlar → Uygulamalar → Yüklü uygulamalar → Kitt → Kaldır**, ya da orijinal
MSI'ı yükseltilmiş (elevated) bir kabuktan `msiexec /x kitt-<versiyon>-x64.msi`
komutuyla çalıştır. Kaldırma işlemi yalnızca kurulan DLL'i ve Kitt'in kendi
registry kayıtlarını siler; başka klavye düzenlerine ya da ayarlara
dokunmaz.

## Gizlilik

Kitt hiçbir şey toplamaz. Somut olarak:

- hiçbir kullanıcı verisi toplanmaz, saklanmaz ya da iletilmez;
- hiçbir zaman ağ bağlantısı kurulmaz;
- telemetri, analitik ya da çökme (crash) raporlama yoktur;
- hesap sistemi yoktur;
- Kitt ne yazdığını göremez ya da kaydedemez — o, seninle işletim sistemi
  arasında duran bir uygulama değil, statik bir native klavye düzenidir.

Tam gerekçe için `KITT_ARCHITECTURE.md` bölüm 16 ("Security Model") ve
bölüm 17'ye ("Privacy") bakabilirsin.

## Geliştirme

Kitt'in eşlemesi tek bir yerde, YAML olarak tanımlanır; geri kalan her şey
(native Windows tabloları, dokümantasyon, testler) bundan üretilir ya da
buna göre doğrulanır. Başlamak için:

- [`installer/README.md`](installer/README.md) — WiX/MSI kurulum paketini
  derleme ve inceleme.
- [`tools/`](tools/) — `build.ps1` (`kittua.dll`'i derler), `package.ps1`
  (MSI'ı derler), `clean.ps1` (build/dist çıktısını temizler).
- [`KITT_ARCHITECTURE.md`](KITT_ARCHITECTURE.md) — tam mimari, build
  sistemi, test stratejisi ve sürümleme politikası.

Hızlı yerel geliştirme döngüsü:

```powershell
pip install -e ".[dev]"
python -m kittgen validate layout/kitt.uk-UA.yaml
python -m kittgen generate
pytest tests/ -v
./tools/build.ps1
./tools/package.ps1
```
