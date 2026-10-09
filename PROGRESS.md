# PROGRESS

Oturumlar arası durum kaydı. Her oturum başında okunur; önemli bir iş bitince veya oturum kapanmadan önce güncellenir.
Proje özeti ve öncelik sırası için bkz. `CLAUDE.md`.

## Son güncelleme
2026-10-09 16:00 (Bakü), koordinatör oturumu (Timmine)

## Durum
- `src.html`: three.js sahne, CodeMirror editör, 4 görev, TR/EN, Web Worker sandbox, AI/Kural koç. **Yeni:** editörde [Kod | Prompt] sekmesi (Prompt modu): öğrenci isteğini yazar, `POST /api/model` sadece açılmış komutlarla kod yazar, sayfa kodu önce worker'da dener, sonra editöre yazar ve `run()` ile sahneyi kurar. Geri al, onay çubuğu, 13 sn zaman aşımı, sunucu/anahtar yoksa veya Kural modundaysa sekme kapalı ve nedenini yazar.
- Komut kilitleri (Farmer tarzı): görev 1 ground/tree/rock, 2 +random, 3 +sun/fog, 4 +house.
- `server/`: koç + yeni `model.py`/`model_validate.py`. Sokratik kapı: diagnose/teach cevabında soru yoksa reddedilir, bir kez yeniden denenir.
- `build.py`: `web/*/*.css|js` dosyalarını `<!-- WEB_MODULES -->` yerine alfabetik inline eder (Senan'ın `web/journey/` için hazır).
- **Gerçek model çalışıyor:** `gemini-3.5-flash-lite` (2026-10-09 doğrulandı). `gemini-2.5-flash` kota hatası (429) veriyor, eski id'ler kaldırılmış. `.env` içine `GEMINI_MODEL=gemini-3.5-flash-lite` yazılmalı (koddaki varsayılan da bu).

## Açık PR'lar (sırayla birleştirilmeli, her biri bir öncekinin üstüne kurulu)
1. #1 `docs/project-brief`: CLAUDE.md proje özeti, dosya sahipliği, koordinatör görevleri; AGENTS.md, GEMINI.md.
2. #2 `feat/infra-socratic`: web/ modül inline + Sokratik kapı + varsayılan model.
3. #3 `feat/prompt-mode`: Prompt modu (sunucu + sayfa + testler).
4. `test/ai-eval`: değerlendirme betiği düzeltmesi, kararsız e2e testi düzeltmesi, gerçek model ölçümleri.
Hepsi sadece Timmine/koordinatör alanına dokunuyor (`src.html`, `server/`, `shared/` (yeni şema, brief'te istendi), `build.py`, `tests/`, `docs/TESTING.md`). Birleştirme için `gh pr merge --admin` gerekir (tek onaylayıcı yok).

## Testler (2026-10-09, ölçülen)
- Birim: 57/57. Tarayıcı: `e2e_browser.py` 33/33 (3 kez üst üste), `e2e_prompt.py` 33/33.
- Gerçek model, 30 vaka: sayfada 26/30 geri bildirim ve 24/30 ipucu AI'dan; AI ipuçlarında sızıntı 0/24; 8 yedeğe düşüşün 5'i bizim paralel testimizin yol açtığı 429.
- Gerçek model, Prompt modu: 11/11 istek çalışan kod üretti, 11/11 sahne sayım kontrolünü geçti, medyan 1,6 sn.
- Uyarı: Gemini ücretsiz katman model başına dakikada 15 istek. Demo sırasında paralel test çalıştırma.
- Ayrıntılar ve gerçek model sonuçları: `docs/TESTING.md`.

## GitHub kurulumu (tamamlandı 2026-10-09)
- `main` koruması: doğrudan push yok, birleştirme için 1 onaylı PR, `enforce_admins` kapalı, force push / dal silme engelli.
- PR #1 (`.gitignore` + `.env.example`) sahibin onayıyla `gh pr merge --admin` ile birleştirildi.
- Not: tek kişiyken PR'lar onay alamaz (kendi PR'ını onaylayamazsın); collaborator gelene kadar `--admin` gerekir.
- [ ] Collaborator'lar: sahip GitHub arayüzünden kendisi ekleyecek.

## Sıradaki işler
1. PR #1, #2, #3 ve `test/ai-eval` PR'ını sırayla birleştir (18:00 hedefi).
2. Pasted brief "additionalProperties" kelimesinde kesildi: Prompt modundan sonraki maddeler (3, 4, ...) koordinatöre ulaşmadı. Tam listeyi yeniden gönder.
3. Kalabalık kullanım için ücretli Gemini katmanı. `RATE_LIMIT_PER_MIN` artık 10 (IP başına); ama sınır IP başına olduğu için birden fazla kullanıcı birlikte yine Google'ın 15/dk sınırını aşabilir.
4. Herkese açık demo: sunucu barındırılmalı (Isa: Dockerfile, deploy/); yoksa yayındaki sayfa kural tabanlı koçla çalışır ve Prompt sekmesi kapalıdır.
5. Senan'ın `web/journey/` modülü geldiğinde `python build.py` ile otomatik inline olur.
