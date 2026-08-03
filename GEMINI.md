# OTT Premium Frontend - Project Documentation

## 1. Project Overview
**AURELION** is a premium Over-The-Top (OTT) streaming platform frontend built with React. It mimics the user experience of major streaming services like Netflix, featuring a dynamic content catalog, user authentication simulation, personal watchlists, and rich UI interactions.

**Key Features:**
*   **Dynamic Content:** Fetches real-time movie and TV show data from The Movie Database (TMDB) API.
*   **Immersive UI:** High-quality animations using Framer Motion (page transitions, hover effects, modal interactions).
*   **User System:** Simulated Authentication (Login/Signup) and Profile management using `localStorage`.
*   **"My List" Feature:** Persisted watchlist functionality.
*   **Responsive Design:** Fully responsive layout built with Tailwind CSS.

## 2. Technology Stack

*   **Core:** React 18
*   **Build Tool:** Vite
*   **Styling:** Tailwind CSS (Utility-first), Custom CSS for scrollbars.
*   **Routing:** React Router DOM (v6/v7 compatible usage).
*   **Animation:** Framer Motion (`AnimatePresence`, `motion.div`).
*   **Icons:** Lucide React.
*   **Data Source:** 
    *   **Primary:** TMDB API (The Movie Database).
    *   **Secondary:** Local Mock Data (used for Search functionality).
*   **Video:** `react-player` (implied usage), `iframe` for YouTube embeds.
*   **React Native:** *Note: The project contains a `components/HeroTrailer.js` file which is a React Native component, likely an artifact or for a separate mobile build.*

## 3. Architecture & File Structure

### root
*   **`GEMINI.md`**: This context file.
*   **`vite.config.js`**: Vite configuration.
*   **`tailwind.config.js`**: Tailwind configuration.
*   **`package.json`**: Dependencies and scripts.

### src/
*   **`main.jsx`**: Application entry point. Mounts the React app.
*   **`App.jsx`**: The core application logic.
    *   **Routing:** Defines Public (`/login`, `/signup`) and Protected Routes (`/`, `/movies`, `/profile`, etc.).
    *   **Global State:** Manages `user` (auth state), `loading` (splash screen), and `myList` (watchlist).
    *   **Persistence:** Syncs `myList` to `localStorage`.
*   **`index.css`**: Global styles and Tailwind directives.

### src/api/
*   **`tmdb.js`**: 
    *   Contains the **TMDB API Key** (Hardcoded).
    *   `requests` object: Maps endpoints (Trending, Top Rated, etc.).
    *   `fetchMovies()`: Helper to fetch and normalize data from TMDB.
    *   `fetchTrailer()`: Helper to find YouTube trailer keys.

### src/components/
This directory contains the building blocks of the UI.

#### Layout & Navigation
*   **`Navbar.jsx`**: 
    *   Fixed top navigation that becomes opaque on scroll.
    *   **Search:** Implements a search overlay using *local mock data* (`src/data/mockData.js`), not the API.
    *   **Notifications:** UI-only notification dropdown.
*   **`AuthLayout.jsx`**: A shared layout wrapper for `Login` and `Signup` screens featuring a background image and glassmorphism card.
*   **`PageLayout.jsx`**: 
    *   Reusable layout for category pages (Movies, Series, New).
    *   Fetches specific data types based on props.
    *   **Filtering:** Implements client-side filtering for **Genre** and **Language**.
*   **`LoadingScreen.jsx`**: An animated splash screen displayed on initial load.

#### Feature Components
*   **`Hero.jsx`**: 
    *   The "Billboard" component at the top of the Home page.
    *   Fetches a random "Now Playing" movie.
    *   Plays the trailer in the background (muted) if available.
    *   Mute/Unmute toggle.
*   **`ContentRow.jsx`**: 
    *   Horizontal scrolling list for movie categories.
    *   Handles hover states (delayed modal trigger).
*   **`MovieModal.jsx`**: 
    *   Detailed view overlay.
    *   Plays the trailer.
    *   Displays metadata (rating, year, synopsis) and fake reviews.
    *   Actions: Play (stub), Add/Remove from My List.
*   **`MyList.jsx`**: 
    *   Grid view of the user's saved content.
    *   Handles removal of items.
*   **`Profile.jsx`**: 
    *   User settings dashboard.
    *   **Edit Profile:** Updates user details in `localStorage`.
    *   **Simulated Features:** Plan management, Payment methods, Settings (visual only).
*   **`Login.jsx` / `Signup.jsx`**: 
    *   Handle user authentication logic against `localStorage`.

#### Legacy / Other
*   **`HeroTrailer.js`** (in root `components/`): **React Native** component. Not used in the web app.

### src/data/
*   **`mockData.js`**: Contains static movie/series data. Currently used primarily by the **Search** feature in `Navbar.jsx`.

## 4. Data Flow & State Management

1.  **Authentication:** 
    *   User data is stored in `localStorage` under key `registeredUser`.
    *   `App.jsx` holds the active `user` state.
    *   Login validates against `localStorage`; Signup writes to it.
2.  **Content Data:**
    *   **Home/Browsing:** Data is fetched from TMDB via `src/api/tmdb.js`.
    *   **Search:** Data is filtered locally from `src/data/mockData.js`.
3.  **User Preferences (My List):**
    *   Managed in `App.jsx` state (`myList`).
    *   Persisted to `localStorage` key `myList`.
    *   Passed down as props to `Hero`, `ContentRow`, `PageLayout`, etc.

## 5. Development Instructions

### Prerequisites
*   Node.js (v16+)
*   npm or yarn

### Setup
```bash
npm install
```

### Running the Dev Server
```bash
npm run dev
```

### Building for Production
```bash
npm run build
```

### Notes & Known Issues
*   **API Key:** The TMDB API key is exposed in the client-side code (`src/api/tmdb.js`). In a real production environment, this should be proxied via a backend.
*   **Search Discrepancy:** The Search bar searches local mock data, while the main browsing experience uses the live API. These datasets may not match.
*   **React Native File:** `components/HeroTrailer.js` should be ignored or removed for the web build.