# Kitt

**Kitt**, Türkçe Q klavyeni kullanarak Ukraynaca yazabilmeni sağlayan bir
program. Klavyendeki tuşların sesi Ukraynaca harflere nasıl benziyorsa, o
mantıkla çalışır — yani ayrı bir Ukraynaca klavye almana, ekranda beliren
bir klavye uygulaması kullanmana ya da sürekli açık duran bir programa
ihtiyacın olmaz.

Kitt kurulduktan sonra, Windows'un normal klavye dili listesine eklenir —
tıpkı İngilizce ya da başka bir dil klavyesi gibi. Görev çubuğunda ayrı bir
simgesi yoktur, arka planda çalışmaz; sadece bir klavye dili gibi orada
durur, sen kullanmak istediğinde seçersin.

## Kitt ne değildir

- Klavyeni değiştiren/yeniden düzenleyen bir uygulama değildir.
- Arka planda sürekli çalışan bir program değildir.
- İnternet bağlantısı gerektiren bir servis değildir.
- Ekranda beliren bir sanal klavye değildir.

Kitt aslında çok küçük iki parçadan oluşur: Windows'un tanıdığı bir klavye
dosyası, ve bunu bilgisayarına yükleyen basit bir kurulum programı. Teknik
detaylarla ilgileniyorsan [`KITT_ARCHITECTURE.md`](KITT_ARCHITECTURE.md)
dosyasına bakabilirsin — ama kullanmak için buna hiç gerek yok.

## Hangi Windows sürümlerinde çalışır

- Windows 10 (64-bit)
- Windows 11 (64-bit)

## Nasıl kurulur

1. Projenin [Releases](../../releases) sayfasından en güncel
   `kitt-<sürüm>-x64.msi` dosyasını indir.
2. İndirdiğin dosyaya çift tıkla. Windows senden izin isteyecek
   (ekranda "Bu uygulamanın değişiklik yapmasına izin veriyor musun?"
   gibi bir pencere çıkar) — **Evet** de. Bu normaldir; bir klavye dili
   eklemek, Windows'un bunu sistemin geneline tanıtmasını gerektirir.
3. Kurulum sihirbazındaki adımları takip et.
4. **Kurulum bittikten sonra bilgisayarını yeniden başlat.** Bu önemli —
   yeniden başlatmadan Kitt, klavye diller arasında geçiş yaptığın kısayolda
   (Windows tuşu + Boşluk) görünmeyebilir.
5. Yeniden başlattıktan sonra Kitt'i ekle:
   **Ayarlar → Saat ve Dil → Dil ve bölge**, kullandığın dilin yanındaki
   **Klavye ekle** butonuna tıkla, listeden **Kitt**'i seç.

Bilgisayarında Python, .NET gibi ekstra bir program kurulu olmasına gerek
yok — Kitt kendi başına çalışan, hazır derlenmiş küçük bir dosyadır.

## Nasıl kullanılır

Kitt eklendikten sonra, diğer klavye dilleri arasında nasıl geçiş
yapıyorsan Kitt'e de öyle geçersin:

- **Windows tuşu + Boşluk** — eklediğin klavye dilleri arasında sırayla
  geçiş yapar.
- Ya da görev çubuğunun sağ altındaki dil göstergesine tıklayıp
  listeden **Kitt**'i seç.

Kitt seçiliyken yazmak, normal bir klavye gibi çalışır:

- **Shift** tuşuyla birlikte basarsan büyük harf çıkar.
- **Caps Lock** beklediğin gibi çalışır.
- Virgül, nokta gibi noktalama işaretleri klavyendeki yerlerinde kalır,
  değişmez.
- Ukraynacada birlikte söylenen bazı sesli harfler (`я`, `ю`, `є`, `ї`)
  için önce **Y** tuşuna, sonra ilgili sesli harfe basman gerekir
  (yalnız `Y`'ye basıp bırakırsan `й` çıkar). Bu, o harflerin Ukraynacada
  gerçekten nasıl söylendiğine dayanıyor.

Hangi tuşun hangi Ukraynaca harfi ürettiğinin tam listesi için
[`docs/mapping.md`](docs/mapping.md) dosyasına bakabilirsin.

## Nasıl kaldırılır

Kitt'i diğer programlar gibi kaldırabilirsin:
**Ayarlar → Uygulamalar → Yüklü uygulamalar**, listede **Kitt**'i bul,
**Kaldır**'a tıkla. Bu işlem yalnızca Kitt'i siler; başka hiçbir klavye
dilini ya da ayarını etkilemez.

## Gizlilik

Kitt hiçbir şeyini toplamaz:

- Ne yazdığını görmez, kaydetmez.
- İnternete hiç bağlanmaz.
- Kullanım istatistiği, hata raporu gibi hiçbir veri göndermez.
- Hesap oluşturmanı istemez.

Kitt, aralarında hiçbir aracı olmadan doğrudan Windows'un kendi klavye
sistemiyle çalışan basit bir dosyadır — teknik detay için
`KITT_ARCHITECTURE.md` dosyasındaki "Security Model" ve "Privacy"
bölümlerine bakabilirsin.

---

## Geliştirme

Bu bölüm, Kitt'in kodunu incelemek ya da geliştirmek isteyenler için.

Kitt'in klavye eşlemesi tek bir YAML dosyasında tanımlanır; geri kalan her
şey (Windows'un anlayacağı dosyalar, dokümantasyon, testler) bundan
otomatik üretilir. Başlamak için:

- [`installer/README.md`](installer/README.md) — kurulum paketini (MSI)
  nasıl derleyip inceleyeceğin.
- [`tools/`](tools/) — `build.ps1` (`kittua.dll`'i derler), `package.ps1`
  (MSI'ı derler), `clean.ps1` (derleme çıktısını temizler).
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
