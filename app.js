/**
 * BibleMapper Scripture Loader
 * Fetches JSON scripture data and renders it cleanly into the HTML container.
 */

// Function to fetch and load a scripture JSON file
async function loadScripture(filePath) {
    const container = document.getElementById('scripture-container');
    
    try {
        // Show a loading indicator while fetching
        container.innerHTML = '<p class="loading">Loading scripture text...</p>';

        const response = await fetch(filePath);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        renderScripture(data);

    } catch (error) {
        console.error("Error loading scripture data:", error);
        container.innerHTML = `<p class="error">Failed to load scripture content. Please verify file path: <code>${filePath}</code></p>`;
    }
}

/**
 * Parses JSON structure and injects formatted HTML into DOM
 */
function renderScripture(data) {
    const container = document.getElementById('scripture-container');
    container.innerHTML = ''; // Clear loading state or previous text

    // Check if valid text array exists
    if (!data || !Array.isArray(data.text)) {
        container.innerHTML = '<p class="error">Invalid scripture format.</p>';
        return;
    }

    // Loop through each chapter in data.text
    data.text.forEach(chapter => {
        const chapterElement = document.createElement('article');
        chapterElement.className = 'chapter';
        chapterElement.id = chapter.ID; // e.g., "OT:1KI.1"

        // Chapter Title (e.g., "1 Kings 1")
        const titleElement = document.createElement('h2');
        titleElement.className = 'chapter-title';
        titleElement.textContent = chapter.name;
        chapterElement.appendChild(titleElement);

        // Verses Container
        const paragraphElement = document.createElement('p');
        paragraphElement.className = 'chapter-text';

        // Loop through each verse in chapter.text
        if (Array.isArray(chapter.text)) {
            chapter.text.forEach(verse => {
                const verseWrapper = document.createElement('span');
                verseWrapper.className = 'verse';
                verseWrapper.id = `${chapter.ID}.${verse.ID}`;

                // Verse number superscript
                const verseNum = document.createElement('sup');
                verseNum.className = 'verse-number';
                verseNum.textContent = verse.ID;

                // Verse text content
                const verseText = document.createTextNode(` ${verse.text} `);

                verseWrapper.appendChild(verseNum);
                verseWrapper.appendChild(verseText);
                paragraphElement.appendChild(verseWrapper);
            });
        }

        chapterElement.appendChild(paragraphElement);
        container.appendChild(chapterElement);
    });
}

// Automatically load default scripture on page initialization
document.addEventListener('DOMContentLoaded', () => {
    // Example relative path matching your repository structure:
    // Update filename/path depending on your translation name (e.g., ESV.json)
    const defaultFilePath = 'BibleMapper_Data/1KI/ESV.json'; 
    loadScripture(defaultFilePath);
});