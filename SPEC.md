# Language Learning Flashcard App Specification

## 1. Project Overview
- **Project Name:** LinguaFlip
- **Type:** Web Application (Flask)
- **Summary:** A simple, elegant flashcard application for language learning. Users can create, manage, and study flashcard decks with a spaced repetition system.
- **Target Users:** Language learners who want a distraction-free tool to memorize vocabulary.

## 2. UI/UX Specification

### Layout Structure
- **Header:** App title ("LinguaFlip"), Navigation (Decks, Add Card, Study), minimal styling.
- **Main Content:** Centered container for deck list or flashcard interface.
- **Footer:** Simple copyright/credits.

### Visual Design
- **Color Palette:**
  - Background: `#f8f9fa` (Light Gray)
  - Card Front: `#ffffff` (White)
  - Card Back: `#e3f2fd` (Soft Blue)
  - Primary Accent: `#4a90e2` (Blue)
  - Text: `#2c3e50` (Dark Slate)
  - Success: `#27ae60` (Green)
  - Error: `#e74c3c` (Red)
- **Typography:**
  - Headings: "Merriweather", serif (for a classic, learning feel)
  - Body: "Open Sans", sans-serif (clean and readable)
- **Spacing:** Generous padding (20px+) for a clean, uncluttered look.
- **Effects:**
  - Card flip animation (3D transform)
  - Subtle shadows on cards: `box-shadow: 0 4px 6px rgba(0,0,0,0.1)`

### Components
- **Deck List:** Grid of deck cards showing deck name and card count.
- **Flashcard:** Large central card with flip animation. Shows front (word) on click, back (translation) on flip.
- **Controls:** "Flip", "Know It", "Still Learning" buttons below card.
- **Add Card Form:** Simple inputs for Front (Word), Back (Translation), Deck selection.

## 3. Functionality Specification

### Core Features
1.  **Deck Management:** Create new decks, view list of decks.
2.  **Card Management:** Add new cards to a deck (Front/Back text).
3.  **Study Mode:**
    -   Show cards one by one from a selected deck.
    -   Flip card to reveal answer.
    -   Mark as "Know It" (remove from session or boost score) or "Still Learning" (show again soon).
4.  **Persistence:** Save decks and cards to a local SQLite database.

### User Flows
1.  **Home:** View all decks. Click deck to study.
2.  **Add Card:** Select deck, enter front/back text, save.
3.  **Study:** Enter deck -> See Front -> Click Flip -> See Back -> Rate knowledge -> Next card.

### Data Handling
-   Use SQLite (`flashcards.db`).
-   Tables: `decks` (id, name), `cards` (id, deck_id, front, back, status).

## 4. Acceptance Criteria
-   App starts with `python app.py`.
-   User can create a deck.
-   User can add cards to a deck.
-   User can study a deck and flip cards.
-   "Know It" moves to next card; "Still Learning" keeps it in rotation.
-   UI is responsive and cards have flip animation.