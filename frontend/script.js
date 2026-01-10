document.addEventListener('DOMContentLoaded', () => {
    const imageInput = document.getElementById('imageInput');
    const fileName = document.getElementById('fileName');
    const colorSlider = document.getElementById('colorSlider');
    const colorValue = document.getElementById('colorValue');
    const convertBtn = document.getElementById('convertBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const loading = document.getElementById('loading');
    const imageContainer = document.getElementById('imageContainer');
    const placeholderText = document.getElementById('placeholderText');
    const paletteContainer = document.getElementById('paletteContainer');
    const paletteGrid = document.getElementById('paletteGrid');

    // Language Elements
    const langIt = document.getElementById('langIt');
    const langEn = document.getElementById('langEn');
    const translatableElements = document.querySelectorAll('[data-i18n]');

    // Translations
    const translations = {
        it: {
            placeholder: "Carica un'immagine per iniziare",
            processing: "Elaborazione in corso...",
            appTitle: "Immagine -> SVG",
            chooseImage: "Scegli Immagine",
            noFile: "Nessun file",
            colorsTitle: "Numero dei colori SVG",
            convertBtn: "Converti in SVG",
            downloadBtn: "Scarica SVG",
            paletteTitle: "Palette",
            errorMsg: "Errore durante la conversione",
            smoothingTitle: "Modalità Smoothing",
            smoothingLight: "Leggero",
            smoothingAggressive: "Aggressivo"
        },
        en: {
            placeholder: "Upload an image to start",
            processing: "Processing...",
            appTitle: "Image -> SVG",
            chooseImage: "Choose Image",
            noFile: "No file selected",
            colorsTitle: "Number of SVG Colors",
            convertBtn: "Convert to SVG",
            downloadBtn: "Download SVG",
            paletteTitle: "Palette",
            errorMsg: "Error during conversion",
            smoothingTitle: "Smoothing Mode",
            smoothingLight: "Light",
            smoothingAggressive: "Aggressive"
        }
    };

    let currentLang = 'it';

    // Language Functions
    function setLanguage(lang) {
        currentLang = lang;
        
        // Update Buttons UI
        if (lang === 'it') {
            langIt.classList.add('active');
            langEn.classList.remove('active');
        } else {
            langEn.classList.add('active');
            langIt.classList.remove('active');
        }

        // Update Text
        translatableElements.forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (translations[lang][key]) {
                el.textContent = translations[lang][key];
            }
        });

        // Update document title if needed, but it's not data-i18n
        document.title = lang === 'it' ? 'Raster to SVG Converter' : 'Raster to SVG Converter';
    }

    langIt.addEventListener('click', () => setLanguage('it'));
    langEn.addEventListener('click', () => setLanguage('en'));

    let selectedFile = null;

    // Handle File Selection
    imageInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            selectedFile = e.target.files[0];
            fileName.textContent = selectedFile.name;
            convertBtn.disabled = false;
            
            // Hide SVG/Download if exists
            downloadBtn.classList.add('hidden');
            paletteContainer.classList.add('hidden');

            // Preview Original
            const reader = new FileReader();
            reader.onload = (e) => {
                placeholderText.classList.add('hidden');
                imageContainer.innerHTML = `<img src="${e.target.result}" alt="Original">`;
            };
            reader.readAsDataURL(selectedFile);
        }
    });

    // Handle Slider Change
    colorSlider.addEventListener('input', (e) => {
        colorValue.textContent = e.target.value;
    });

    // Handle Conversion
    convertBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        // UI Updates
        loading.classList.remove('hidden');
        convertBtn.disabled = true;
        paletteContainer.classList.add('hidden');
        downloadBtn.classList.add('hidden');
        
        // Reset Progress
        const progressBar = document.getElementById('progressBar');
        const progressPercentage = document.getElementById('progressPercentage');
        const loadingStatus = document.getElementById('loadingStatus');
        progressBar.style.width = '0%';
        progressPercentage.textContent = '0%';
        loadingStatus.textContent = translations[currentLang].processing;

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('colors', colorSlider.value);
        
        const smoothingMode = document.querySelector('input[name="smoothing"]:checked').value;
        formData.append('smoothing', smoothingMode);

        try {
            // 1. Start Conversion Task
            const response = await fetch('/convert', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Error: ${response.statusText}`);
            }

            const data = await response.json();
            const taskId = data.task_id;

            // 2. Poll Status
            await pollStatus(taskId);

        } catch (error) {
            console.error(error);
            const msg = translations[currentLang].errorMsg || "Error";
            alert(`${msg}: ${error.message}`);
            loading.classList.add('hidden');
            convertBtn.disabled = false;
        }
    });

    async function pollStatus(taskId) {
        const progressBar = document.getElementById('progressBar');
        const progressPercentage = document.getElementById('progressPercentage');
        const loadingStatus = document.getElementById('loadingStatus');

        const pollInterval = setInterval(async () => {
            try {
                const res = await fetch(`/status/${taskId}`);
                if (!res.ok) throw new Error("Status check failed");
                
                const statusData = await res.json();
                
                // Update Progress UI
                if (statusData.progress) {
                    progressBar.style.width = `${statusData.progress}%`;
                    progressPercentage.textContent = `${statusData.progress}%`;
                }
                
                if (statusData.message) {
                    // Optional: Translate status messages if needed, or just show backend message
                    loadingStatus.textContent = statusData.message;
                }

                if (statusData.status === 'completed') {
                    clearInterval(pollInterval);
                    finishConversion(statusData.result);
                } else if (statusData.status === 'error') {
                    clearInterval(pollInterval);
                    throw new Error(statusData.message);
                }
                
            } catch (error) {
                clearInterval(pollInterval);
                console.error(error);
                const msg = translations[currentLang].errorMsg || "Error";
                alert(`${msg}: ${error.message}`);
                loading.classList.add('hidden');
                convertBtn.disabled = false;
            }
        }, 500);
    }

    function finishConversion(data) {
        const svgText = data.svg;
        const palette = data.palette;

        // Display SVG (Replace original image)
        imageContainer.innerHTML = svgText;

        // Adjust SVG to fit container
        const svgElement = imageContainer.querySelector('svg');
        if(svgElement) {
            if (!svgElement.hasAttribute('viewBox')) {
                const w = svgElement.getAttribute('width');
                const h = svgElement.getAttribute('height');
                if (w && h) {
                    const valW = parseFloat(w);
                    const valH = parseFloat(h);
                    if (!isNaN(valW) && !isNaN(valH)) {
                        svgElement.setAttribute('viewBox', `0 0 ${valW} ${valH}`);
                    }
                }
            }

            svgElement.removeAttribute('width');
            svgElement.removeAttribute('height');
            svgElement.setAttribute('width', '100%');
            svgElement.setAttribute('height', '100%');
            svgElement.style.width = '100%';
            svgElement.style.height = '100%';
            
            if (!svgElement.hasAttribute('preserveAspectRatio')) {
                svgElement.setAttribute('preserveAspectRatio', 'xMidYMid meet');
            }
        }

        // Display Palette
        displayPalette(palette);

        // Setup Download
        const blob = new Blob([svgText], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        downloadBtn.href = url;
        downloadBtn.classList.remove('hidden');

        // Hide Loading
        loading.classList.add('hidden');
        convertBtn.disabled = false;
    }


    function displayPalette(palette) {
        paletteGrid.innerHTML = ''; // Clear previous
        paletteContainer.classList.remove('hidden');

        palette.forEach((color, index) => {
            const item = document.createElement('div');
            item.className = 'palette-item';
            item.style.backgroundColor = color;
            item.textContent = index + 1;
            item.title = color; // Tooltip with hex code
            paletteGrid.appendChild(item);
        });
    }
});
