# Rencana: uji korektor Sonnet (Uji A) dan kelanjutan I q.12–13

Ditulis 2026-09-28, sebagai serah terima ke sesi baru. Sesi lama terlalu panjang: sesi
utama memakai sekitar 55% batas, summa-reviewer 21%, general-purpose 18%,
summa-translator 6%.

## Status

- **Selesai (`ai-reviewed`, ada di manifest):** I prolog, q.1–11.
- **q.12–13:** sudah dikoreksi Opus (commit `47788d5`), tetapi `q012.review.json` /
  `q013.review.json` belum ada karena sesi terputus. Perlu satu reviewer **delta-mode**
  untuk memeriksa hasil koreksinya dan menulis log. Bandingkan dengan draf di commit
  `2f79da9`, lalu rekam dengan `record.py` dan render.
- **Belum di-deploy.** Pemilik menunggu I q.3–13 selesai. Setelah itu:
  `render.py`, preview, lalu deploy.

## Uji A: apakah korektor Latin boleh memakai Sonnet?

- **Kontrol:** koreksi Opus untuk q.7 dan q.8.
  - Draf sebelum koreksi: `git show 2f79da9:translations/summa/i/q007.json` (dan q008).
  - Temuan Opus: `translations/summa/i/q007.review.json` dan `q008.review.json`
    (28 dan 25 temuan).
- **Mengapa bukan q.1–2:** `pelajaran.md` sekarang memuat aturan yang lahir dari koreksi
  q.1–2, jadi Sonnet akan "mendapat bocoran".
- **Cara menjalankan:**
  1. Salin kedua draf ke scratch.
  2. Beri Sonnet `pelajaran.md` versi commit `2f79da9` (sebelum q.3–13 dikoreksi) dan
     tabel istilah seragam.
  3. Jalankan korektor Sonnet (`summa-reviewer` dengan `model: sonnet`) pada kedua draf.
  4. Satu penilai Opus mencocokkan daftar temuan *major/critical* Opus dengan hasil
     Sonnet: ditemukan / terlewat / Sonnet membuat perubahan yang salah.
- **Kriteria:**
  - Sonnet menemukan ≥ 90% temuan major/critical Opus dan tidak menambah kesalahan →
    korektor dipindah ke Sonnet; Opus hanya memeriksa sampel (misalnya 1 dari 5
    pertanyaan).
  - Di bawah itu → korektor tetap Opus.
- **Penerjemah tidak diuji:** porsinya hanya 6% dari batas.

## Penghematan lain

- Korektor hanya diberi baris tabel istilah dan pelajaran yang relevan untuk
  pertanyaannya, bukan seluruh file.
- Maksimal 2–3 agen paralel.
- Orkestrator di sesi baru boleh memakai Sonnet.

## Tingkat effort (reasoning)

| Peran | Model | Effort |
|---|---|---|
| Sesi utama / orkestrator | Sonnet | rendah |
| summa-translator | Opus (tetap) | sedang |
| summa-reviewer (korektor Latin) | Opus, atau Sonnet jika lolos Uji A | tinggi |
| Penilai Uji A | Opus | tinggi (sekali jalan) |

- Uji A membandingkan **Sonnet effort tinggi** dengan Opus, supaya yang diuji benar-benar
  modelnya, bukan effort-nya.
- Effort subagen diatur di frontmatter `.claude/agents/*.md`. **Pastikan dulu nama kolom
  frontmatter-nya di dokumentasi Claude Code sebelum menambahkannya.** Effort sesi utama
  diatur di aplikasi, bersama pilihan model.
