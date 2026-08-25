# Kitt

Kitt, Türkçe Q klavyenizi kullanarak Ukraynaca yazmanızı sağlayan bir
programdır. Bastığınız tuşun sesi Ukraynaca harfe benziyorsa o harfi
yazar. Ayrı bir Ukraynaca klavye almanıza, ekran klavyesi kullanmanıza
ya da sürekli açık duran bir programa ihtiyacınız yoktur.

Kurulduktan sonra Windows'un normal klavye dili listesine eklenir, tıpkı
İngilizce ya da başka bir dil klavyesi gibi. Görev çubuğunda ayrı bir
simgesi olmaz, arka planda çalışmaz. Sadece listede durur, ihtiyacınız
olduğunda seçersiniz.

## Kitt ne değildir

- Klavyenizi değiştiren bir uygulama değildir.
- Arka planda çalışan bir program değildir.
- İnternet bağlantısı isteyen bir servis değildir.
- Ekran klavyesi değildir.

Kitt aslında iki küçük parçadan oluşur: Windows'un tanıdığı bir klavye
dosyası ve bunu bilgisayarınıza yükleyen basit bir kurulum programı.
Teknik detay istiyorsanız [`KITT_ARCHITECTURE.md`](KITT_ARCHITECTURE.md)
dosyasına bakabilirsiniz, ama kullanmak için gerekmiyor.

## Hangi Windows sürümlerinde çalışır

- Windows 10 (64-bit)
- Windows 11 (64-bit)

Kitt, Türkçe Q klavye düzeni için yapıldı. Laptop, masaüstü, harici,
kablosuz fark etmez, hepsi aynı tuş sinyalini gönderdiği için aynı
şekilde çalışır. Türkçe F kullanıyorsanız Kitt sizi karıştırır, çünkü
harfler F değil Q dizilimine göre eşlendi. Bu durumda ya klavyenizi
Windows üzerinden Türkçe Q'ya çevirmeniz (fiziksel klavyeyi
değiştirmenize gerek yok, sadece ayardan) ya da Kitt'i kullanmamanız
gerekir.

Hangi düzeni kullandığınızı görmek için: Ayarlar > Saat ve Dil > Dil ve
bölge, dilinizin altındaki klavye listesine bakın, "Türkçe Q" mu
"Türkçe F" mi yazıyor. Bu, aşağıda Kitt'i ekleyeceğiniz listeden farklı
bir yer; burada kontrol ettiğiniz, tuşlarınıza şu an neyin karşılık
geldiği.

## Kurulum

1. [Releases](../../releases) sayfasından en güncel
   `kitt-<sürüm>-x64.msi` dosyasını indirin.
2. Dosyaya çift tıklayın. Windows izin isteyecek, Evet deyin. Bu normal,
   çünkü bir klavye dili eklemek Windows'un bunu sisteme tanıtmasını
   gerektiriyor.
3. Kurulum sihirbazını takip edin.
4. Kurulum bittikten sonra bilgisayarınızı yeniden başlatın. Bu adımı
   atlarsanız Kitt, klavyeler arası geçiş kısayolunda (Windows tuşu +
   Boşluk) görünmeyebilir.
5. Yeniden başlattıktan sonra Kitt'i ekleyin: Ayarlar > Saat ve Dil >
   Dil ve bölge, dilinizin yanındaki Klavye ekle butonuna tıklayın,
   listeden Kitt'i seçin.

Bilgisayarınızda Python, .NET gibi ekstra bir şey kurulu olmasına
gerek yok. Kitt kendi başına çalışan, hazır derlenmiş küçük bir
dosyadır.

## Kullanım

Kitt eklendikten sonra diğer klavye dilleri arasında nasıl geçiş
yapıyorsanız Kitt'e de öyle geçersiniz:

- Windows tuşu + Boşluk, eklediğiniz diller arasında sırayla geçer.
- Ya da görev çubuğundaki dil göstergesine tıklayıp Kitt'i seçin.

Kitt seçiliyken yazmak normal bir klavye gibi çalışır:

- Shift ile birlikte basarsanız büyük harf çıkar.
- Caps Lock beklediğiniz gibi çalışır.
- Virgül, nokta gibi noktalama işaretleri yerinde kalır, değişmez.
- Ukraynacada birlikte söylenen bazı sesli harfler (я, ю, є, ї) için
  önce Y tuşuna, sonra ilgili sesli harfe basmanız gerekir. Sadece
  Y'ye basıp bırakırsanız й çıkar. Bu, o harflerin Ukraynacada
  gerçekten nasıl söylendiğine dayanıyor.

Hangi tuşun hangi Ukraynaca harfi ürettiğinin tam listesi için
[`docs/mapping.md`](docs/mapping.md) dosyasına bakabilirsiniz.

## Kaldırma

Kaldırmadan önce mümkünse Kitt'ten başka bir klavye diline geçin
(Windows tuşu + Boşluk). Kitt o an aktif olarak kullanılıyorsa Windows
silinecek dosyayı kilitli tutabilir ve kaldırma işlemi yeniden başlatma
isteyebilir.

Kitt'i diğer programlar gibi kaldırabilirsiniz: Ayarlar > Uygulamalar
> Yüklü uygulamalar, listede Kitt'i bulun, Kaldır'a tıklayın. Bu işlem
yalnızca Kitt'i siler, başka klavye diline ya da ayarına dokunmaz.

## Gizlilik

Kitt hiçbir şey toplamaz.

- Ne yazdığınızı görmez, kaydetmez.
- İnternete bağlanmaz.
- Kullanım istatistiği ya da hata raporu göndermez.
- Hesap oluşturmanızı istemez.

Kitt, aracı olmadan doğrudan Windows'un kendi klavye sistemiyle çalışan
basit bir dosyadır. Teknik detay için `KITT_ARCHITECTURE.md`
dosyasındaki "Security Model" ve "Privacy" bölümlerine bakabilirsiniz.

---

## Geliştirme

Bu bölüm Kitt'in kodunu incelemek ya da geliştirmek isteyenler için.

Kitt'in klavye eşlemesi tek bir YAML dosyasında tanımlanır, geri kalan
her şey (Windows dosyaları, dokümantasyon, testler) bundan otomatik
üretilir. Başlamak için:

- [`installer/README.md`](installer/README.md): kurulum paketini (MSI)
  nasıl derleyip inceleyeceğiniz.
- [`tools/`](tools/): `build.ps1` (`kittua.dll`'i derler), `package.ps1`
  (MSI'ı derler), `clean.ps1` (derleme çıktısını temizler).
- [`KITT_ARCHITECTURE.md`](KITT_ARCHITECTURE.md): tam mimari, build
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

## Lisans

Kitt, [MIT Lisansı](LICENSE) ile dağıtılır.
