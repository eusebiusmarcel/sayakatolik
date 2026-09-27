# Panduan gaya bahasa: terjemahan Summa

**Pembaca sasaran:** umat Katolik Indonesia yang terpelajar tetapi bukan filsuf atau
teolog. Mereka harus bisa memahami argumen Thomas tanpa kamus filsafat. Ketepatan isi
tetap mutlak (lihat ADR 0001), tetapi **bentuk kalimat melayani pembaca Indonesia,
bukan susunan Latin**.

Panduan ini **mengikat** penerjemah (`summa-translator`) dan penyunting
(`summa-editor`). Jika bertentangan dengan `glosarium.md`, glosarium yang menang untuk
istilah, dan panduan ini yang menang untuk bentuk kalimat.

## 1. Prinsip utama: uraikan, jangan menjiplak

Istilah teknis yang tidak dikenal pembaca awam **diuraikan menjadi kalimat yang
jelas**. Jangan hanya dipindahkan kata demi kata.

> *verum convertitur cum ente*
> ✗ "yang benar itu dapat dipertukarkan (konvertibel) dengan pengada"
> ✓ "setiap hal yang ada itu benar, dan setiap hal yang benar itu ada"

Istilah Latin boleh dicantumkan dalam kurung sesudah uraiannya, pada kemunculan
pertama di satu halaman, jika istilah itu penting bagi pembaca yang ingin mendalami.

## 2. Kata sambung dan awal kalimat

- **Jangan memulai kalimat dengan "Dan", "Tetapi", "Sebab", atau "Karena".**
  - *Et* di awal kalimat: gabungkan dengan kalimat sebelumnya, atau pakai "Selain itu",
    "Lagi pula", atau "Demikian pula".
  - *Sed* → "Akan tetapi" atau "Namun".
  - *Enim* → "Sebab, …" hanya di dalam kalimat. Jika perlu memulai kalimat baru, pakai
    "Hal itu karena …" atau "Alasannya, …".
- *Unde* / *ergo* / *igitur* → "Oleh karena itu", "Maka", "Jadi". Variasikan; jangan
  mengulang kata yang sama tiga kali berturut-turut.
- *Autem* sering tidak perlu diterjemahkan sama sekali.

## 3. Rujukan harus jelas

Kata "ini", "itu", "ia", dan "-nya" yang rujukannya tidak jelas **wajib dieksplisitkan**.

> *Scriptura sacra huius doctrinae*
> ✗ "Kitab Suci ajaran ini"
> ✓ "Kitab Suci, yang menjadi dasar ajaran suci ini"

*Haec doctrina* / *haec scientia* → "ajaran suci ini" atau "ilmu suci ini", bukan
sekadar "ajaran ini".

## 4. Kalimat panjang boleh dipecah

- Periode Latin yang panjang **boleh dipecah menjadi beberapa kalimat**, dan urutan
  anak kalimat boleh disusun ulang, **asalkan**:
  - jumlah paragraf per bagian tetap sama (diperiksa oleh lint);
  - tidak ada unsur makna yang hilang atau bertambah;
  - hubungan logisnya tetap eksplisit (sebab–akibat, syarat, pertentangan).
- Dalam satu kalimat, jangan menumpuk lebih dari dua anak kalimat dengan "yang".

## 5. Diksi

- Hindari "yang mana" dan "di mana" sebagai kata penghubung relatif. Pakai "yang",
  "tempat", atau pecah kalimatnya.
- Hindari tumpukan kalimat pasif. Jika pelakunya jelas, pakai kalimat aktif.
- Kata serapan teknis ("aktus", "potensi", "substansi", dan sebagainya) dipakai sesuai
  glosarium. Istilah yang baru pertama kali muncul di satu halaman boleh diberi uraian
  singkat dalam kurung.
- Ikuti EYD V dan KBBI: "keniscayaan", "mesti", dan seterusnya.

## 6. Judul

- Judul pertanyaan dan artikel ditulis dengan **huruf kapital hanya di awal kalimat**
  dan pada nama diri, bukan huruf kapital gaya Inggris.
  - ✗ "Apakah dalam Kitab Suci Satu Rumusan Teks Dapat Memiliki Beberapa Makna?"
  - ✓ "Apakah dalam Kitab Suci satu rumusan teks dapat memiliki beberapa makna?"
- Judul artikel berbentuk pertanyaan yang diakhiri "?". Judul pertanyaan (quaestio)
  berbentuk frasa benda: "Hakikat dan cakupan ajaran suci".

## 7. Yang tidak boleh diubah oleh penyuntingan

- Rumus struktural di glosarium §A ("Sebaliknya", "Aku menjawab: harus dikatakan
  bahwa", "Tampaknya", "Selanjutnya", "Harus dikatakan bahwa").
- Istilah berstatus `disetujui` di glosarium.
- Kutipan Kitab Suci beserta rujukannya. Hanya bahasanya yang boleh diperhalus, dan
  tetap harus setia pada Latin Thomas (ADR 0001 §4).
