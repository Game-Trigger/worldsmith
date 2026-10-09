# PROGRESS

Oturumlar arası durum kaydı. Her oturum başında okunur; önemli bir iş bitince veya oturum kapanmadan önce güncellenir.
Proje özeti ve öncelik sırası için bkz. `CLAUDE.md`.

## Son güncelleme
2026-10-09

## Durum
- `src.html`: çalışan tek sayfalık demo (three.js sahne, CodeMirror editör, 4 görev, TR/EN, Web Worker'da kullanıcı kodu) + AI koç istemcisi (AI / Kural anahtarı, sunucu yoksa kural tabanlı yedek, etiketli).
- `server/`: Python (sadece standart kütüphane) AI koç sunucusu. Gemini/Claude adaptörü, şema doğrulama, çözüm sızıntı kapısı, bir yeniden deneme, önbellek, IP başına hız sınırı, kullanım logu. `shared/` altında sözleşmeler, `content/lessons.json` ders verisi.
- Testler: 36 sunucu testi geçti, 33 tarayıcı kontrolü geçti, 30 vakalık değerlendirme kural koç için ölçüldü (`docs/TESTING.md`).
- **Henüz yapılmadı:** koç gerçek bir modelle hiç çalıştırılmadı (anahtar yok). `.env.example` içindeki model adları doğrulanmadı.
- Repo: https://github.com/T1mmine/worldsmith (public). `gh` kurulu, T1mmine olarak giriş yapılmış.

## GitHub kurulumu (tamamlandı 2026-10-09)
- `main` koruması: doğrudan push yok, birleştirme için 1 onaylı PR, `enforce_admins` kapalı, force push / dal silme engelli.
- PR #1 (`.gitignore` + `.env.example`) sahibin onayıyla `gh pr merge --admin` ile birleştirildi.
- Not: tek kişiyken PR'lar onay alamaz (kendi PR'ını onaylayamazsın); collaborator gelene kadar `--admin` gerekir.
- [ ] Collaborator'lar: sahip GitHub arayüzünden kendisi ekleyecek.

## Sıradaki işler
1. Gemini anahtarı al (aistudio.google.com), `.env` dosyasına yaz, `python server/app.py` ile dört görevi elle dene.
2. `python tests/run_eval.py --mode ai` çalıştır, sayıları `docs/TESTING.md` içine yaz, reddedilen cevaplara göre `server/coach.py` istemini düzelt.
3. Şartnamedeki "daha önce geliştirilmiş ürün" kuralını kontrol et. Demo 2026-10-08'de yapıldı, `docs/DISCLOSURE.md` bunu açıkça yazıyor.
4. Herkese açık adres: sunucu bir yerde barındırılmalı, yoksa yayındaki sayfa kural tabanlı koçla çalışır.
5. Solver-doğrulamalı görev üretimi (CLAUDE.md #2), sonra Farmer tarzı bot görevleri (#3).
