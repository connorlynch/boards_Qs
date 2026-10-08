# Boards Flashcards

Audio flashcards for radiation oncology oral boards.

- **Read**: the first tap reads the question aloud, the second reads (and shows) the answer.
- **Flag**: saves the card for later. Pick "Flagged for review" in the topic menu to study only those.
- **Next**: moves to another card in the chosen topic. It goes through every card once before repeating any.
- The topic menu filters by disease site.
- Audio is recorded clips (in `audio/`), so it plays through CarPlay, Bluetooth and the lock screen like music. In the car, the play button reads the next part of the card, next track goes to a new card and reads its question, and previous track repeats.

`questions.json` holds the question bank (437 items). Edit it to add or fix questions, then change `VERSION` in `sw.js` so installed copies update. Edited or new cards use the phone's built-in voice until their audio is re-rendered with `python3 tools/make_audio.py <voice.onnx>` (instructions at the top of that script). Flags and settings are stored in the browser on each device.

Sources: the owner's oral boards review decks and notes, plus "APS Boards Condensed". This is a study aid, not clinical guidance.
