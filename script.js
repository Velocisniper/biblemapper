// ==========================================
// GAME DATA STRUCTURES
// ==========================================

const otBooks = [
    { id: "GEN", chapters: 50, testament: "OT" }, { id: "EXO", chapters: 40, testament: "OT" },
    { id: "LEV", chapters: 27, testament: "OT" }, { id: "NUM", chapters: 36, testament: "OT" },
    { id: "DEU", chapters: 34, testament: "OT" }, { id: "JOS", chapters: 24, testament: "OT" },
    { id: "JDG", chapters: 21, testament: "OT" }, { id: "RUT", chapters: 4, testament: "OT" },
    { id: "1SA", chapters: 31, testament: "OT" }, { id: "2SA", chapters: 24, testament: "OT" },
    { id: "1KI", chapters: 22, testament: "OT" }, { id: "2KI", chapters: 25, testament: "OT" },
    { id: "1CH", chapters: 29, testament: "OT" }, { id: "2CH", chapters: 36, testament: "OT" },
    { id: "EZR", chapters: 10, testament: "OT" }, { id: "NEH", chapters: 13, testament: "OT" },
    { id: "EST", chapters: 10, testament: "OT" }, { id: "JOB", chapters: 42, testament: "OT" },
    { id: "PSA", chapters: 150, testament: "OT" }, { id: "PRO", chapters: 31, testament: "OT" },
    { id: "ECC", chapters: 12, testament: "OT" }, { id: "SNG", chapters: 8, testament: "OT" },
    { id: "ISA", chapters: 66, testament: "OT" }, { id: "JER", chapters: 52, testament: "OT" },
    { id: "LAM", chapters: 5, testament: "OT" }, { id: "EZE", chapters: 48, testament: "OT" },
    { id: "DAN", chapters: 12, testament: "OT" }, { id: "HOS", chapters: 14, testament: "OT" },
    { id: "JOE", chapters: 3, testament: "OT" }, { id: "AMO", chapters: 9, testament: "OT" },
    { id: "OBA", chapters: 1, testament: "OT" }, { id: "JON", chapters: 4, testament: "OT" },
    { id: "MIC", chapters: 7, testament: "OT" }, { id: "NAH", chapters: 3, testament: "OT" },
    { id: "HAB", chapters: 3, testament: "OT" }, { id: "ZEP", chapters: 3, testament: "OT" },
    { id: "HAG", chapters: 2, testament: "OT" }, { id: "ZEC", chapters: 14, testament: "OT" },
    { id: "MAL", chapters: 4, testament: "OT" }
];

const gospels = [
    { id: "MAT", chapters: 28, testament: "NT" },
    { id: "MRK", chapters: 16, testament: "NT" },
    { id: "LUK", chapters: 24, testament: "NT" },
    { id: "JHN", chapters: 21, testament: "NT" }
];

const acts = [
    { id: "ACT", chapters: 28, testament: "NT" }
];

const ntLetters = [
    { id: "ROM", chapters: 16, testament: "NT" },
    { id: "1CO", chapters: 16, testament: "NT" },
    { id: "2CO", chapters: 13, testament: "NT" },
    { id: "GAL", chapters: 6, testament: "NT" },
    { id: "EPH", chapters: 6, testament: "NT" },
    { id: "PHP", chapters: 4, testament: "NT" },
    { id: "COL", chapters: 4, testament: "NT" },
    { id: "1TH", chapters: 5, testament: "NT" },
    { id: "2TH", chapters: 3, testament: "NT" },
    { id: "1TI", chapters: 6, testament: "NT" },
    { id: "2TI", chapters: 4, testament: "NT" },
    { id: "TIT", chapters: 3, testament: "NT" },
    { id: "PHM", chapters: 1, testament: "NT" },
    { id: "HEB", chapters: 13, testament: "NT" },
    { id: "JAS", chapters: 5, testament: "NT" },
    { id: "1PE", chapters: 5, testament: "NT" },
    { id: "2PE", chapters: 3, testament: "NT" },
    { id: "1JN", chapters: 5, testament: "NT" },
    { id: "2JN", chapters: 1, testament: "NT" },
    { id: "3JN", chapters: 1, testament: "NT" },
    { id: "JUD", chapters: 1, testament: "NT" },
    { id: "REV", chapters: 22, testament: "NT" }
];

const ntBooks = [...gospels, ...acts, ...ntLetters];


// ==========================================
// NEW CATEGORY GROUPS
// ==========================================

// Torah = Genesis through Deuteronomy
const torahBooks = otBooks.slice(0, 5);

// Historical Books = Joshua through Esther
const historicalBooks = otBooks.slice(5, 17);


// ==========================================
// BIBLE STRUCTURE
// ==========================================

const bibleStructure = {
    "Old Testament": otBooks,
    "New Testament": ntBooks,
    "Gospels": gospels,
    "Acts": acts,
    "Torah": torahBooks,
    "Historical Books": historicalBooks,
    "Entire Bible": [...otBooks, ...ntBooks]
};


// ==========================================
// GLOBAL DATA STRUCTURES
// ==========================================

let validMapLocations = [];
let locationCoordinates = {};
let locationFeatures = {};
let locationScriptureNames = {};

let currentTargetLocation = null;
let currentTargetCenter = null;
let currentTargetVerseText = "";
let currentTargetReference = null;

let isDailyGame = false;
let activeSettings = {
    showLabels: true
};

let totalRounds = 3;
let currentRound = 1;
let roundScores = [];
let guessSubmitted = false;

let dailyDateString = "";
let dailySection = "";


// ==========================================
// TIMER VARIABLES
// ==========================================

let countdownInterval;
let timeRemaining;


// ==========================================
// SEEDED RNG LOGIC
// ==========================================

let seededRandom = Math.random;

function xmur3(str) {

    for (
        var i = 0, h = 1779033703 ^ str.length;
        i < str.length;
        i++
    ) {

        h = Math.imul(
            h ^ str.charCodeAt(i),
            3432918353
        );

        h =
            h << 13 |
            h >>> 19;
    }

    return function () {

        h = Math.imul(
            h ^ (h >>> 16),
            2246822507
        );

        h = Math.imul(
            h ^ (h >>> 13),
            3266489909
        );

        return (
            h ^= h >>> 16
        ) >>> 0;
    };
}


function mulberry32(a) {

    return function () {

        var t = a += 0x6D2B79F5;

        t =
            Math.imul(
                t ^ t >>> 15,
                t | 1
            );

        t ^=
            t +
            Math.imul(
                t ^ t >>> 7,
                t | 61
            );

        return (
            (t ^ t >>> 14) >>> 0
        ) / 4294967296;
    };
}


function initDailySeed() {

    const d = new Date();

    dailyDateString =
        `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;

    const seedGen =
        xmur3(dailyDateString);

    seededRandom =
        mulberry32(seedGen());
}


// ==========================================
// UI NAVIGATION & STATE
// ==========================================

const startMenu =
    document.getElementById('start-menu');

const customMenu =
    document.getElementById('custom-menu');

const summaryMenu =
    document.getElementById('summary-menu');

const btnGotoCustom =
    document.getElementById('btn-goto-custom');

const btnBackMain =
    document.getElementById('btn-back-main');

const btnStartCustom =
    document.getElementById('btn-start-custom');

const btnDaily =
    document.getElementById('btn-daily');

const btnSummaryHome =
    document.getElementById('btn-summary-home');

const btnShare =
    document.getElementById('btn-share');

const submitBtn =
    document.getElementById('submit-guess-btn');

const nextBtn =
    document.getElementById('next-round-btn');

const verseRevealBox =
    document.getElementById('verse-reveal-box');

const timerDisplay =
    document.getElementById('timer-display');


const inputs = {

    translation:
        document.getElementById('setting-translation'),

    book:
        document.getElementById('setting-book'),

    keyword:
        document.getElementById('setting-keyword'),

    labels:
        document.getElementById('setting-labels'),

    time:
        document.getElementById('setting-time'),

    rounds:
        document.getElementById('setting-rounds')
};


// ==========================================
// SETTINGS
// ==========================================

function loadSettings() {

    if (localStorage.getItem('bm_translation'))
        inputs.translation.value =
            localStorage.getItem('bm_translation');

    if (localStorage.getItem('bm_book'))
        inputs.book.value =
            localStorage.getItem('bm_book');

    if (localStorage.getItem('bm_keyword'))
        inputs.keyword.checked =
            localStorage.getItem('bm_keyword') === 'true';

    if (localStorage.getItem('bm_labels'))
        inputs.labels.checked =
            localStorage.getItem('bm_labels') === 'true';

    if (localStorage.getItem('bm_time'))
        inputs.time.value =
            localStorage.getItem('bm_time');

    if (localStorage.getItem('bm_rounds'))
        inputs.rounds.value =
            localStorage.getItem('bm_rounds');
}


function saveSettings() {

    localStorage.setItem(
        'bm_translation',
        inputs.translation.value
    );

    localStorage.setItem(
        'bm_book',
        inputs.book.value
    );

    localStorage.setItem(
        'bm_keyword',
        inputs.keyword.checked
    );

    localStorage.setItem(
        'bm_labels',
        inputs.labels.checked
    );

    localStorage.setItem(
        'bm_time',
        inputs.time.value
    );

    let r =
        parseInt(inputs.rounds.value);

    if (r < 1)
        r = 1;

    if (r > 10)
        r = 10;

    inputs.rounds.value = r;

    localStorage.setItem(
        'bm_rounds',
        r
    );
}


Object.values(inputs).forEach(
    input =>
        input.addEventListener(
            'change',
            saveSettings
        )
);


// ==========================================
// CUSTOM GAME
// ==========================================

btnGotoCustom.addEventListener(
    'click',
    () => {

        startMenu.style.display = 'none';
        customMenu.style.display = 'flex';

        loadSettings();
    }
);


btnBackMain.addEventListener(
    'click',
    () => {

        customMenu.style.display = 'none';
        startMenu.style.display = 'flex';
    }
);


btnStartCustom.addEventListener(
    'click',
    () => {

        saveSettings();

        isDailyGame = false;

        seededRandom = Math.random;

        activeSettings = {

            translation:
                inputs.translation.value,

            book:
                inputs.book.value,

            showKeyword:
                inputs.keyword.checked,

            showLabels:
                inputs.labels.checked,

            timeLimit:
                inputs.time.value,

            rounds:
                parseInt(inputs.rounds.value)
        };

        totalRounds =
            activeSettings.rounds;

        currentRound = 1;

        roundScores = [];

        customMenu.style.display = 'none';

        updateLabels();

        startRound();
    }
);


// ==========================================
// DAILY GAME
// ==========================================

btnDaily.addEventListener(
    'click',
    () => {

        isDailyGame = true;

        initDailySeed();

        const sections = [

            "Entire Bible",

            "Old Testament",

            "New Testament",

            "Gospels",

            "Acts",

            "Torah",

            "Historical Books"
        ];

        dailySection =
            sections[
                Math.floor(
                    seededRandom() *
                    sections.length
                )
            ];

        activeSettings = {

            translation: 'ESV',

            book: dailySection,

            showKeyword: false,

            showLabels: true,

            // DAILY GAME = 90 SECONDS
            timeLimit: '90',

            rounds: 3
        };

        totalRounds =
            activeSettings.rounds;

        currentRound = 1;

        roundScores = [];

        startMenu.style.display = 'none';

        updateLabels();

        startRound();
    }
);


// ==========================================
// HOW-TO MODAL
// ==========================================

const howToBtn =
    document.getElementById('btn-how-to');

const howToModal =
    document.getElementById('how-to-modal');

const closeModalBtn =
    document.getElementById('close-modal');


howToBtn.addEventListener(
    'click',
    () =>
        howToModal.style.display = 'flex'
);


closeModalBtn.addEventListener(
    'click',
    () =>
        howToModal.style.display = 'none'
);


window.addEventListener(
    'click',
    (e) => {

        if (e.target === howToModal)
            howToModal.style.display = 'none';
    }
);


// ==========================================
// MAP INITIALIZATION
// ==========================================

const defaultCenter =
    [31.7683, 35.2137];


const map =
    L.map(
        'map',
        {
            maxBounds:
                L.latLngBounds(
                    L.latLng(0, -15),
                    L.latLng(55, 95)
                ),

            maxBoundsViscosity: 1.0,

            minZoom: 4,

            maxZoom: 18
        }
    ).setView(
        defaultCenter,
        6
    );


L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}',
    {
        attribution: 'Tiles &copy; Esri',

        maxNativeZoom: 13,

        maxZoom: 18
    }
).addTo(map);


let playerGuessMarker = null;

let targetMarker = null;

let resultLine = null;

let resultBoundary = null;

let labelGroup =
    L.featureGroup().addTo(map);

let allLabels = [];


// ==========================================
// MAP CLICK
// ==========================================

map.on(
    'click',
    function (e) {

        if (guessSubmitted)
            return;

        if (playerGuessMarker) {

            playerGuessMarker.setLatLng(
                e.latlng
            );

        } else {

            playerGuessMarker =
                L.circleMarker(
                    e.latlng,
                    {
                        radius: 7,

                        fillColor: "#ff0000",

                        color: "#ffffff",

                        weight: 2,

                        opacity: 1,

                        fillOpacity: 1
                    }
                ).addTo(map);
        }

        if (submitBtn.disabled) {

            submitBtn.disabled = false;

            submitBtn.classList.remove(
                'btn-disabled'
            );
        }
    }
);


// ==========================================
// LOAD GEOJSON
// ==========================================

fetch('./bible_places.geojson')
    .then(
        response =>
            response.json()
    )
    .then(
        geojsonData => {

            L.geoJSON(
                geojsonData,
                {

                    style:
                        function (feature) {

                            if (
                                feature.properties.is_water
                            ) {

                                return {

                                    color: '#9EBCD8',

                                    weight: 3,

                                    opacity: 0.9,

                                    fillOpacity: 0
                                };
                            }

                            return {

                                opacity: 0,

                                fillOpacity: 0,

                                weight: 0
                            };
                        },


                    pointToLayer:
                        function (
                            feature,
                            latlng
                        ) {

                            return L.circleMarker(
                                latlng,
                                {

                                    opacity: 0,

                                    fillOpacity: 0,

                                    radius: 0
                                }
                            );
                        },


                    onEachFeature:
                        function (
                            feature,
                            layer
                        ) {

                            const importance =
                                feature.properties.importance;

                            const internalName =
                                feature.properties.name;

                            const center =
                                feature.properties.center;


                            /*
                             * New fields supplied by
                             * kmlprocess.py:
                             *
                             * scripture_name
                             * references
                             */

                            const scriptureName =
                                feature.properties.scripture_name ||
                                internalName;


                            if (internalName) {

                                const internalLower =
                                    internalName.toLowerCase();

                                const scriptureLower =
                                    scriptureName.toLowerCase();


                                locationCoordinates[
                                    internalLower
                                ] = center;


                                locationFeatures[
                                    internalLower
                                ] = feature;


                                locationScriptureNames[
                                    internalLower
                                ] = scriptureLower;


                                if (
                                    !validMapLocations.includes(
                                        scriptureLower
                                    )
                                ) {

                                    validMapLocations.push(
                                        scriptureLower
                                    );
                                }
                            }


                            let fontSize =
                                importance === 1
                                    ? '18px'
                                    : importance === 2
                                        ? '16px'
                                        : importance === 3
                                            ? '13px'
                                            : '11px';


                            let fontWeight =
                                importance === 1
                                    ? '900'
                                    : importance === 2
                                        ? '800'
                                        : importance === 3
                                            ? 'bold'
                                            : 'normal';


                            const marker =
                                L.marker(
                                    [
                                        center[1],
                                        center[0]
                                    ],
                                    {

                                        icon:
                                            L.divIcon(
                                                {

                                                    className:
                                                        'map-place-label',

                                                    html:
                                                        `<span style="font-size: ${fontSize}; font-weight: ${fontWeight};">${scriptureName}</span>`,

                                                    iconSize:
                                                        null
                                                }
                                            ),

                                        interactive:
                                            false
                                    }
                                );


                            marker.importance =
                                importance;

                            allLabels.push(
                                marker
                            );


                            if (
                                feature.properties.is_water
                            ) {

                                layer.addTo(map);
                            }
                        }
                }
            ).addTo(map);


            updateLabels();

            map.on(
                'zoomend',
                updateLabels
            );
        }
    )
    .catch(
        err =>
            console.error(
                "Map data failed to load!",
                err
            )
    );


// ==========================================
// LABEL VISIBILITY
// ==========================================

function updateLabels() {

    if (!activeSettings.showLabels) {

        labelGroup.clearLayers();

        return;
    }

    const currentZoom =
        map.getZoom();


    let maxAllowedRank =
        currentZoom <= 6
            ? 1
            : currentZoom === 7
                ? 2
                : currentZoom === 8
                    ? 3
                    : 4;


    labelGroup.clearLayers();


    allLabels.forEach(
        marker => {

            if (
                marker.importance <=
                maxAllowedRank
            ) {

                labelGroup.addLayer(
                    marker
                );
            }
        }
    );
}


// ==========================================
// TIMER
// ==========================================

function startTimer() {

    clearInterval(
        countdownInterval
    );


    const timeSetting =
        activeSettings.timeLimit;


    if (
        timeSetting === 'unlimited'
    ) {

        timerDisplay.style.display =
            'none';

        return;
    }


    timeRemaining =
        parseInt(timeSetting);


    updateTimerDisplay();


    timerDisplay.style.display =
        'block';

    timerDisplay.classList.remove(
        'timer-warning'
    );


    countdownInterval =
        setInterval(
            () => {

                timeRemaining--;

                updateTimerDisplay();


                if (
                    timeRemaining <= 10
                ) {

                    timerDisplay.classList.add(
                        'timer-warning'
                    );
                }


                if (
                    timeRemaining <= 0
                ) {

                    clearInterval(
                        countdownInterval
                    );

                    processGuess(true);
                }

            },
            1000
        );
}


function stopTimer() {

    clearInterval(
        countdownInterval
    );

    timerDisplay.style.display =
        'none';
}


function updateTimerDisplay() {

    const m =
        Math.floor(
            timeRemaining / 60
        );

    const s =
        timeRemaining % 60;


    timerDisplay.innerText =
        `${m}:${s < 10 ? '0' : ''}${s}`;
}


// ==========================================
// SCRIPTURE REFERENCE HELPERS
// ==========================================

function getVerseReference(
    bookData,
    chapter,
    verse
) {

    const bookId =
        bookData.id ||
        bookData.book ||
        "";


    const chapterNumber =
        chapter.chapter ||
        chapter.number ||
        chapter.id ||
        "";


    const verseNumber =
        verse.ID ||
        verse.id ||
        verse.number ||
        "";


    if (
        !bookId ||
        !chapterNumber ||
        !verseNumber
    ) {

        return null;
    }


    return `${bookId} ${chapterNumber}:${verseNumber}`;
}


// ==========================================
// REFERENCE RANGE MATCHING
// ==========================================

function referenceMatchesVerse(
    reference,
    bookId,
    chapterNumber,
    verseNumber
) {

    if (!reference)
        return false;


    const cleaned =
        reference
            .toUpperCase()
            .replace(/\s+/g, '')
            .replace(/[–—]/g, '-');


    const targetBook =
        String(bookId).toUpperCase();


    const targetChapter =
        parseInt(
            chapterNumber
        );


    const targetVerse =
        parseInt(
            verseNumber
        );


    /*
     * Examples:
     *
     * ACT 11:19
     * ACT 13:14
     * JDG 8:5-16
     */

    const match =
        cleaned.match(
            /^(.+?)(\d+):(\d+)(?:-(?:(\d+):)?(\d+))?$/
        );


    if (!match)
        return false;


    const refBook =
        match[1];


    const startChapter =
        parseInt(match[2]);


    const startVerse =
        parseInt(match[3]);


    const endChapter =
        match[4]
            ? parseInt(match[4])
            : startChapter;


    const endVerse =
        match[5]
            ? parseInt(match[5])
            : startVerse;


    if (
        refBook !== targetBook
    ) {

        return false;
    }


    if (
        targetChapter < startChapter ||
        targetChapter > endChapter
    ) {

        return false;
    }


    if (
        startChapter === endChapter
    ) {

        return (
            targetChapter === startChapter &&
            targetVerse >= startVerse &&
            targetVerse <= endVerse
        );
    }


    if (
        targetChapter === startChapter
    ) {

        return targetVerse >= startVerse;
    }


    if (
        targetChapter === endChapter
    ) {

        return targetVerse <= endVerse;
    }


    return true;
}


// ==========================================
// FEATURE / VERSE MATCHING
// ==========================================

function featureMatchesVerse(
    feature,
    bookData,
    chapter,
    verse
) {

    if (
        !feature ||
        !feature.properties
    ) {

        return false;
    }


    const references =
        feature.properties.references;


    if (
        !Array.isArray(references) ||
        references.length === 0
    ) {

        return false;
    }


    const bookId =
        bookData.id ||
        bookData.book ||
        "";


    const chapterNumber =
        chapter.chapter ||
        chapter.number ||
        chapter.id ||
        "";


    const verseNumber =
        verse.ID ||
        verse.id ||
        verse.number ||
        "";


    return references.some(
        reference =>
            referenceMatchesVerse(
                reference,
                bookId,
                chapterNumber,
                verseNumber
            )
    );
}


// ==========================================
// RESOLVE AMBIGUOUS LOCATIONS
// ==========================================

function resolveLocationFeature(
    scriptureName,
    bookData,
    chapter,
    verse
) {

    const candidates = [];


    Object.keys(
        locationFeatures
    ).forEach(
        internalName => {

            const feature =
                locationFeatures[
                    internalName
                ];


            const featureScriptureName =
                locationScriptureNames[
                    internalName
                ];


            if (
                featureScriptureName ===
                scriptureName
            ) {

                candidates.push(
                    feature
                );
            }
        }
    );


    if (
        candidates.length === 0
    ) {

        return null;
    }


    /*
     * Normal location:
     * only one geographic feature.
     */

    if (
        candidates.length === 1
    ) {

        return candidates[0];
    }


    /*
     * Ambiguous location:
     * use KML-derived references.
     */

    const matching =
        candidates.filter(
            feature =>
                featureMatchesVerse(
                    feature,
                    bookData,
                    chapter,
                    verse
                )
        );


    if (
        matching.length > 0
    ) {

        return matching[0];
    }


    return null;
}


// ==========================================
// GAME LOOP
// ==========================================

function startRound() {

    guessSubmitted = false;


    document.getElementById(
        'reopen-verse-btn'
    ).style.display = 'none';


    verseRevealBox.style.display =
        'none';


    nextBtn.style.display =
        'none';


    if (playerGuessMarker) {

        map.removeLayer(
            playerGuessMarker
        );

        playerGuessMarker = null;
    }


    if (targetMarker) {

        map.removeLayer(
            targetMarker
        );

        targetMarker = null;
    }


    if (resultLine) {

        map.removeLayer(
            resultLine
        );

        resultLine = null;
    }


    if (resultBoundary) {

        map.removeLayer(
            resultBoundary
        );

        resultBoundary = null;
    }


    currentTargetLocation =
        null;

    currentTargetCenter =
        null;

    currentTargetReference =
        null;


    map.setView(
        defaultCenter,
        6
    );


    submitBtn.style.display =
        'block';


    submitBtn.disabled =
        true;


    submitBtn.classList.add(
        'btn-disabled'
    );


    findPlayableVerse(
        activeSettings.book,
        activeSettings.translation
    );
}


// ==========================================
// FIND PLAYABLE VERSE
// ==========================================

function findPlayableVerse(
    sectionName,
    translation,
    attempts = 0
) {

    if (
        attempts > 15
    ) {

        alert(
            "Could not find a verse with a map location in this section. Please try a different book."
        );

        return;
    }


    if (
        validMapLocations.length === 0
    ) {

        return;
    }


    const sectionBooks =
        bibleStructure[
            sectionName
        ] ||
        bibleStructure["Acts"];


    const randomBook =
        sectionBooks[
            Math.floor(
                seededRandom() *
                sectionBooks.length
            )
        ];


    const filePath =
        `./BibleMapper_Data/${randomBook.testament}/${randomBook.id}/${translation}.json`;


    fetch(filePath)
        .then(
            response => {

                if (!response.ok) {

                    throw new Error(
                        `HTTP ${response.status}`
                    );
                }

                return response.json();
            }
        )
        .then(
            bookData => {

                if (
                    !processAndDisplayScripture(
                        bookData,
                        randomBook
                    )
                ) {

                    findPlayableVerse(
                        sectionName,
                        translation,
                        attempts + 1
                    );
                }
            }
        )
        .catch(
            err => {

                findPlayableVerse(
                    sectionName,
                    translation,
                    attempts + 1
                );
            }
        );
}


// ==========================================
// PROCESS SCRIPTURE
// ==========================================

function processAndDisplayScripture(
    bookData,
    randomBook
) {

    let validVerses = [];


    if (
        !bookData.text ||
        !Array.isArray(bookData.text)
    ) {

        return false;
    }


    bookData.text.forEach(
        chapter => {

            if (
                !chapter.text ||
                !Array.isArray(chapter.text)
            ) {

                return;
            }


            chapter.text.forEach(
                verse => {

                    const verseTextLower =
                        verse.text.toLowerCase();


                    let matchedLocation =
                        null;


                    /*
                     * Find Scripture-facing
                     * location name.
                     *
                     * This allows:
                     *
                     * Succoth
                     *
                     * to match either:
                     *
                     * Succoth|egypt
                     * Succoth|israel
                     */

                    const containsMapLocation =
                        validMapLocations.some(
                            location => {

                                const escaped =
                                    location.replace(
                                        /[.*+?^${}()|[\]\\]/g,
                                        '\\$&'
                                    );


                                if (
                                    new RegExp(
                                        `\\b${escaped}\\b`,
                                        'i'
                                    ).test(
                                        verseTextLower
                                    )
                                ) {

                                    matchedLocation =
                                        location;

                                    return true;
                                }


                                return false;
                            }
                        );


                    if (
                        !containsMapLocation
                    ) {

                        return;
                    }


                    /*
                     * Resolve the exact geographic
                     * feature for this verse.
                     */

                    const resolvedFeature =
                        resolveLocationFeature(
                            matchedLocation,
                            bookData,
                            chapter,
                            verse
                        );


                    /*
                     * If this is an ambiguous
                     * location and no feature has
                     * a matching Scripture
                     * reference, don't use it.
                     */

                    if (
                        !resolvedFeature
                    ) {

                        return;
                    }


                    const internalName =
                        resolvedFeature
                            .properties
                            .name
                            .toLowerCase();


                    validVerses.push({

                        chapterData:
                            chapter,

                        targetVerse:
                            verse,

                        matchedWord:
                            matchedLocation,

                        feature:
                            resolvedFeature,

                        internalName:
                            internalName
                    });
                }
            );
        }
    );


    if (
        validVerses.length === 0
    ) {

        return false;
    }


    const randomIndex =
        Math.floor(
            seededRandom() *
            validVerses.length
        );


    const selection =
        validVerses[
            randomIndex
        ];


    // ==========================================
    // JERUSALEM SKIP
    // 60% CHANCE TO SKIP
    // ==========================================

    if (
        selection.matchedWord ===
        "jerusalem"
    ) {

        if (
            seededRandom() < 0.60
        ) {

            console.log(
                "Jerusalem selected, skipping due to 60% rule."
            );

            return false;
        }
    }


    // ==========================================
    // EGYPT SKIP
    // 20% CHANCE TO SKIP
    // ==========================================

    if (
        selection.matchedWord ===
        "egypt"
    ) {

        if (
            seededRandom() < 0.20
        ) {

            console.log(
                "Egypt selected, skipping due to 20% rule."
            );

            return false;
        }
    }


    // ==========================================
    // SET TARGET
    // ==========================================

    currentTargetLocation =
        selection.internalName;


    currentTargetCenter =
        selection.feature.properties.center;


    currentTargetVerseText =
        selection.targetVerse.text;


    currentTargetReference =
        getVerseReference(
            bookData,
            selection.chapterData,
            selection.targetVerse
        );


    openScriptureWindow(
        selection.chapterData,
        selection.targetVerse,
        selection.matchedWord
    );


    startTimer();


    return true;
}


// ==========================================
// SUBMIT & SCORING
// ==========================================

submitBtn.addEventListener(
    'click',
    function () {

        if (
            this.disabled
        ) {

            return;
        }


        processGuess(false);
    }
);


function processGuess(
    isTimeout = false
) {

    if (
        guessSubmitted
    ) {

        return;
    }


    guessSubmitted = true;


    stopTimer();


    submitBtn.disabled =
        true;


    submitBtn.classList.add(
        'btn-disabled'
    );


    if (
        !playerGuessMarker &&
        !isTimeout
    ) {

        return;
    }


    let score = 0;

    let excl = "";

    let distanceMiles = 0;


    let endLatLng =
        L.latLng(
            currentTargetCenter[1],
            currentTargetCenter[0]
        );


    // ==========================================
    // NO GUESS / TIMEOUT
    // ==========================================

    if (
        !playerGuessMarker &&
        isTimeout
    ) {

        score = 0;

        excl =
            "Time's Up! No guess placed.";


        roundScores.push(
            score
        );


        document.getElementById(
            'scripture-modal'
        ).style.display =
            'none';


        document.getElementById(
            'reopen-verse-btn'
        ).style.display =
            'none';


        showResult(
            endLatLng,
            endLatLng,
            0,
            score,
            excl,
            false,
            true
        );


        return;
    }


    const startLatLng =
        playerGuessMarker.getLatLng();


    const pt =
        turf.point(
            [
                startLatLng.lng,
                startLatLng.lat
            ]
        );


    const feature =
        locationFeatures[
            currentTargetLocation
        ];


    let isInside = false;


    let closestLngLat = [
        currentTargetCenter[0],
        currentTargetCenter[1]
    ];


    // ==========================================
    // POLYGON
    // ==========================================

    if (
        feature.geometry.type ===
            'Polygon' ||
        feature.geometry.type ===
            'MultiPolygon'
    ) {

        isInside =
            turf.booleanPointInPolygon(
                pt,
                feature
            );


        if (!isInside) {

            const lines =
                turf.polygonToLine(
                    feature
                );


            let closest =
                null;

            let minDist =
                Infinity;


            turf.flattenEach(
                lines,
                function (
                    currentFeature
                ) {

                    const snap =
                        turf.nearestPointOnLine(
                            currentFeature,
                            pt,
                            {
                                units:
                                    'miles'
                            }
                        );


                    const d =
                        snap.properties.dist;


                    if (
                        d < minDist
                    ) {

                        minDist = d;

                        closest = snap;
                    }
                }
            );


            if (closest) {

                distanceMiles =
                    minDist;

                closestLngLat =
                    closest
                        .geometry
                        .coordinates;
            }
        }
    }


    // ==========================================
    // LINESTRING / RIVER
    // ==========================================

    else if (
        feature.geometry.type ===
        'LineString'
    ) {

        /*
         * Use the actual nearest point
         * on the river/LineString.
         */

        const snap =
            turf.nearestPointOnLine(
                feature,
                pt,
                {
                    units:
                        'miles'
                }
            );


        distanceMiles =
            snap.properties.dist;


        closestLngLat =
            snap.geometry
                .coordinates;
    }


    // ==========================================
    // OTHER GEOMETRIES
    // ==========================================

    else {

        distanceMiles =
            turf.distance(
                pt,
                feature,
                {
                    units:
                        'miles'
                }
            );
    }


    // ==========================================
    // SCORING
    // ==========================================

    /*
     * GOSPELS:
     *
     * 0 points at 600 miles.
     *
     * Everything else:
     *
     * 0 points at 1000 miles.
     */

    const isGospelGame =
        activeSettings.book ===
        "Gospels";


    const zeroPointDistance =
        isGospelGame
            ? 600
            : 1000;


    if (
        isInside ||
        distanceMiles <= 3
    ) {

        score = 1000;

        distanceMiles = 0;

    } else if (
        distanceMiles >=
        zeroPointDistance
    ) {

        score = 0;

    } else {

        score =
            Math.max(
                0,
                Math.round(
                    1000 *
                    Math.exp(
                        -(distanceMiles - 3) *
                        (
                            Math.log(1000) /
                            (
                                zeroPointDistance - 3
                            )
                        )
                    )
                )
            );
    }


    roundScores.push(
        score
    );


    // ==========================================
    // EXCLAMATION
    // ==========================================

    if (isTimeout) {

        excl =
            "Time's Up!";

    } else {

        let exclamations = [];


        if (
            score === 1000
        ) {

            exclamations = [
                "Perfect!",
                "Great Job!"
            ];

        } else if (
            score >= 900
        ) {

            exclamations = [
                "Great!",
                "Awesome!"
            ];

        } else if (
            score >= 700
        ) {

            exclamations = [
                "Nice Job!",
                "Not Bad!"
            ];

        } else if (
            score >= 400
        ) {

            exclamations = [
                "Alright!",
                "Good Try!"
            ];

        } else {

            exclamations = [
                "Better luck next time.",
                "Too bad."
            ];
        }


        excl =
            exclamations[
                Math.floor(
                    Math.random() *
                    exclamations.length
                )
            ];
    }


    document.getElementById(
        'scripture-modal'
    ).style.display =
        'none';


    document.getElementById(
        'reopen-verse-btn'
    ).style.display =
        'none';


    endLatLng =
        L.latLng(
            closestLngLat[1],
            closestLngLat[0]
        );


    if (
        score === 1000 ||
        distanceMiles === 0
    ) {

        showResult(
            startLatLng,
            endLatLng,
            distanceMiles,
            score,
            excl,
            true,
            false
        );

    } else {

        animateLine(
            startLatLng,
            endLatLng,
            distanceMiles,
            score,
            excl
        );
    }
}


// ==========================================
// RESULT LINE ANIMATION
// ==========================================

function animateLine(
    start,
    end,
    distanceMiles,
    score,
    excl
) {

    if (resultLine)
        map.removeLayer(
            resultLine
        );


    resultLine =
        L.polyline(
            [
                start,
                start
            ],
            {

                color: '#1a1a1a',

                weight: 3,

                dashArray: '8, 8',

                lineCap: 'round',

                opacity: 0.8
            }
        ).addTo(map);


    const duration =
        600;


    const startTime =
        performance.now();


    function step(
        currentTime
    ) {

        const elapsed =
            currentTime -
            startTime;


        const progress =
            Math.min(
                elapsed /
                    duration,
                1
            );


        const easeProgress =
            1 -
            Math.pow(
                1 -
                progress,
                3
            );


        const currentLat =
            start.lat +
            (
                end.lat -
                start.lat
            ) *
            easeProgress;


        const currentLng =
            start.lng +
            (
                end.lng -
                start.lng
            ) *
            easeProgress;


        resultLine.setLatLngs(
            [
                start,
                L.latLng(
                    currentLat,
                    currentLng
                )
            ]
        );


        if (
            progress < 1
        ) {

            requestAnimationFrame(
                step
            );

        } else {

            showResult(
                start,
                end,
                distanceMiles,
                score,
                excl,
                false,
                false
            );
        }
    }


    requestAnimationFrame(
        step
    );
}


// ==========================================
// SHOW RESULT
// ==========================================

function showResult(
    start,
    end,
    distanceMiles,
    score,
    excl,
    isPerfect,
    noGuess = false
) {

    targetMarker =
        L.circleMarker(
            end,
            {

                radius: 7,

                fillColor: "#00ff00",

                color: "#ffffff",

                weight: 2,

                opacity: 1,

                fillOpacity: 1
            }
        ).addTo(map);


    const feature =
        locationFeatures[
            currentTargetLocation
        ];


    if (
        feature &&
        (
            feature.geometry.type ===
                'Polygon' ||
            feature.geometry.type ===
                'MultiPolygon'
        )
    ) {

        resultBoundary =
            L.geoJSON(
                feature,
                {

                    style: {

                        color: '#00ff00',

                        weight: 3,

                        fillColor: '#00ff00',

                        fillOpacity: 0.3
                    },

                    interactive: false
                }
            ).addTo(map);
    }


    const displayLocationName =
        locationScriptureNames[
            currentTargetLocation
        ] ||
        currentTargetLocation;


    const regex =
        new RegExp(
            `\\b${displayLocationName}\\b`,
            'gi'
        );


    const revealedText =
        currentTargetVerseText.replace(
            regex,
            '<strong>$&</strong>'
        );


    let distText =
        noGuess
            ? "No Guess Placed"
            : (
                distanceMiles === 0
                    ? "Inside Territory"
                    : `${distanceMiles.toFixed(1)} miles away`
            );


    verseRevealBox.innerHTML =
        `
        "${revealedText}"
        <span class="score-text">
            ${distText}
            &nbsp;|&nbsp;
            ${score}/1000 Points, ${excl}
        </span>
        `;


    verseRevealBox.style.display =
        'block';


    nextBtn.style.display =
        'block';


    if (noGuess) {

        map.flyTo(
            end,
            8,
            {
                duration: 1.5
            }
        );

    } else if (isPerfect) {

        map.flyTo(
            start,
            9,
            {
                duration: 1.5
            }
        );

    } else {

        const bounds =
            L.latLngBounds(
                start,
                end
            );


        map.flyToBounds(
            bounds,
            {

                padding:
                    [100, 100],

                maxZoom: 10,

                duration: 1.5
            }
        );
    }
}


// ==========================================
// NEXT ROUND & SUMMARY
// ==========================================

nextBtn.addEventListener(
    'click',
    () => {

        if (
            currentRound <
            totalRounds
        ) {

            currentRound++;

            startRound();

        } else {

            showSummary();
        }
    }
);


function showSummary() {

    verseRevealBox.style.display =
        'none';


    nextBtn.style.display =
        'none';


    submitBtn.style.display =
        'none';


    const scoresDiv =
        document.getElementById(
            'summary-scores'
        );


    const averageDiv =
        document.getElementById(
            'summary-average'
        );


    let html = "";

    let sum = 0;


    roundScores.forEach(
        (s, i) => {

            html +=
                `<div>Round ${i + 1}: <strong>${s}</strong></div>`;

            sum += s;
        }
    );


    scoresDiv.innerHTML =
        html;


    let avg =
        Math.round(
            sum /
            roundScores.length
        );


    averageDiv.innerHTML =
        `Average Score: ${avg} / 1000`;


    if (isDailyGame)
        btnShare.style.display =
            'block';

    else
        btnShare.style.display =
            'none';


    summaryMenu.style.display =
        'flex';
}


// ==========================================
// DAILY SHARE
// ==========================================

btnShare.addEventListener(
    'click',
    async () => {

        const getEmoji =
            (score) => {

                if (score >= 800)
                    return '🟩';

                if (score >= 400)
                    return '🟨';

                return '🟥';
            };


        let sum =
            roundScores.reduce(
                (a, b) =>
                    a + b,
                0
            );


        let avg =
            Math.round(
                sum /
                roundScores.length
            );


        let shareText =
            `Daily Bible Mapper -\n` +
            `${dailyDateString} - ${dailySection}\n`;


        roundScores.forEach(
            (score, i) => {

                shareText +=
                    `Round ${i + 1}: ${score} ${getEmoji(score)}\n`;
            }
        );


        shareText +=
            `Average: ${avg} ${getEmoji(avg)}`;


        const isMobile =
            /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i
                .test(
                    navigator.userAgent
                );


        if (
            isMobile &&
            navigator.share
        ) {

            try {

                await navigator.share(
                    {
                        text:
                            shareText
                    }
                );

            } catch (err) {

                console.log(
                    "Share cancelled or failed.",
                    err
                );
            }

        } else {

            navigator.clipboard
                .writeText(
                    shareText
                )
                .then(
                    () => {

                        alert(
                            'Results copied to clipboard!'
                        );
                    }
                )
                .catch(
                    err => {

                        alert(
                            'Failed to copy text.'
                        );
                    }
                );
        }
    }
);


// ==========================================
// RETURN TO MAIN MENU
// ==========================================

btnSummaryHome.addEventListener(
    'click',
    () => {

        summaryMenu.style.display =
            'none';


        startMenu.style.display =
            'flex';


        stopTimer();


        if (playerGuessMarker) {

            map.removeLayer(
                playerGuessMarker
            );

            playerGuessMarker = null;
        }


        if (targetMarker) {

            map.removeLayer(
                targetMarker
            );

            targetMarker = null;
        }


        if (resultLine) {

            map.removeLayer(
                resultLine
            );

            resultLine = null;
        }


        if (resultBoundary) {

            map.removeLayer(
                resultBoundary
            );

            resultBoundary = null;
        }


        map.setView(
            defaultCenter,
            6
        );
    }
);


// ==========================================
// SCRIPTURE MODAL
// ==========================================

function openScriptureWindow(
    chapter,
    targetVerse,
    matchedWord
) {

    const chapterContainer =
        document.getElementById(
            'chapter-text'
        );


    chapterContainer.innerHTML =
        "";


    if (
        chapter.text &&
        Array.isArray(
            chapter.text
        )
    ) {

        chapter.text.forEach(
            verse => {

                const verseSpan =
                    document.createElement(
                        'span'
                    );


                const verseNum =
                    document.createElement(
                        'span'
                    );


                verseNum.className =
                    'verse-number';


                verseNum.innerText =
                    verse.ID ||
                    "";


                let textToDisplay =
                    (verse.text || "") +
                    " ";


                if (
                    !activeSettings.showKeyword &&
                    matchedWord
                ) {

                    const escaped =
                        matchedWord.replace(
                            /[.*+?^${}()|[\]\\]/g,
                            '\\$&'
                        );


                    const regex =
                        new RegExp(
                            `\\b${escaped}\\b`,
                            'gi'
                        );


                    textToDisplay =
                        textToDisplay.replace(
                            regex,
                            '_____'
                        );
                }


                const verseText =
                    document.createTextNode(
                        textToDisplay
                    );


                verseSpan.appendChild(
                    verseNum
                );


                verseSpan.appendChild(
                    verseText
                );


                if (
                    targetVerse &&
                    verse.ID ===
                        targetVerse.ID
                ) {

                    verseSpan.className =
                        'target-verse';
                }


                chapterContainer.appendChild(
                    verseSpan
                );
            }
        );

    } else {

        chapterContainer.innerText =
            "Error loading chapter text.";
    }


    document.getElementById(
        'scripture-modal'
    ).style.display =
        'flex';


    document.getElementById(
        'reopen-verse-btn'
    ).style.display =
        'none';


    setTimeout(
        () => {

            const targetEl =
                document.querySelector(
                    '.target-verse'
                );


            if (targetEl) {

                targetEl.scrollIntoView(
                    {
                        behavior:
                            'smooth',

                        block:
                            'center'
                    }
                );
            }

        },
        100
    );
}


// ==========================================
// MINIMIZE / REOPEN SCRIPTURE
// ==========================================

window.minimizeScriptureWindow =
    function () {

        document.getElementById(
            'scripture-modal'
        ).style.display =
            'none';


        document.getElementById(
            'reopen-verse-btn'
        ).style.display =
            'block';
    };


window.reopenScriptureWindow =
    function () {

        document.getElementById(
            'scripture-modal'
        ).style.display =
            'flex';


        document.getElementById(
            'reopen-verse-btn'
        ).style.display =
            'none';
    };