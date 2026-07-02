document.addEventListener('DOMContentLoaded', () => {
    const imageInput = document.getElementById('imageInput');
    const fileName = document.getElementById('fileName');
    const colorSlider = document.getElementById('colorSlider');
    const colorValue = document.getElementById('colorValue');
    const convertBtn = document.getElementById('convertBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const exitBtn = document.getElementById('exitBtn');
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
            exitBtn: "ESCI",
            paletteTitle: "Palette",
            errorMsg: "Errore durante la conversione",
            smoothingTitle: "Modalità Smoothing",
            smoothingLight: "Leggero",
            smoothingAggressive: "Aggressivo",
            excludeTitle: "Escludi Colore",
            excludeWhite: "Bianco",
            excludeBlack: "Nero"
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
            exitBtn: "EXIT",
            paletteTitle: "Palette",
            errorMsg: "Error during conversion",
            smoothingTitle: "Smoothing Mode",
            smoothingLight: "Light",
            smoothingAggressive: "Aggressive",
            excludeTitle: "Exclude Color",
            excludeWhite: "White",
            excludeBlack: "Black"
        }
    };

    let currentLang = 'en';

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
        document.documentElement.lang = lang;
    }

    langIt.addEventListener('click', () => setLanguage('it'));
    langEn.addEventListener('click', () => setLanguage('en'));
    setLanguage('en');

    let selectedFile = null;
    let selectedFilePath = null;
    let currentSvgContent = null;

    const getTauri = () => window.__TAURI__;
    const isTauriDesktop = () => Boolean(getTauri() && getTauri().core && getTauri().core.invoke);
    const isPywebviewDesktop = () => Boolean(window.pywebview);
    const tauriInvoke = (command, args = {}) => getTauri().core.invoke(command, args);

    function detectMimeType(filename) {
        const filenameLower = filename.toLowerCase();
        if (filenameLower.endsWith('.png')) return 'image/png';
        if (filenameLower.endsWith('.gif')) return 'image/gif';
        if (filenameLower.endsWith('.bmp')) return 'image/bmp';
        if (filenameLower.endsWith('.webp')) return 'image/webp';
        return 'image/jpeg';
    }

    function fileFromBase64(result) {
        const byteCharacters = atob(result.data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const mimeType = detectMimeType(result.filename);
        const blob = new Blob([byteArray], { type: mimeType });
        return new File([blob], result.filename, { type: mimeType });
    }

    function defaultSvgFilename() {
        if (!selectedFile) return 'converted.svg';
        return `${selectedFile.name.replace(/\.[^/.]+$/, '')}.svg`;
    }

    function defaultSvgPath() {
        const filename = defaultSvgFilename();
        if (!selectedFilePath) return filename;

        const separatorIndex = Math.max(selectedFilePath.lastIndexOf('/'), selectedFilePath.lastIndexOf('\\'));
        if (separatorIndex < 0) return filename;

        return `${selectedFilePath.slice(0, separatorIndex + 1)}${filename}`;
    }

    function updateProgress(progress, message) {
        const progressBar = document.getElementById('progressBar');
        const progressPercentage = document.getElementById('progressPercentage');
        const loadingStatus = document.getElementById('loadingStatus');
        progressBar.style.width = `${progress}%`;
        progressPercentage.textContent = `${progress}%`;
        if (message) loadingStatus.textContent = message;
    }

    function wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    async function openImageWithTauri() {
        const dialog = getTauri() && getTauri().dialog;
        if (!dialog || !dialog.open) {
            throw new Error('Tauri dialog plugin is not available');
        }

        const selectedPath = await dialog.open({
            multiple: false,
            directory: false,
            title: 'Open Image',
            filters: [
                {
                    name: 'Image Files',
                    extensions: ['png', 'jpg', 'jpeg', 'bmp', 'webp', 'gif']
                }
            ]
        });

        if (!selectedPath) return;

        const filePath = Array.isArray(selectedPath) ? selectedPath[0] : selectedPath;
        const result = await tauriInvoke('read_image_file', { path: filePath });
        const file = fileFromBase64(result);
        handleFileSelect(file, { path: result.path || filePath });
    }

    async function saveSvgWithTauri() {
        if (!currentSvgContent) return;

        const dialog = getTauri() && getTauri().dialog;
        if (!dialog || !dialog.save) {
            throw new Error('Tauri dialog plugin is not available');
        }

        const savePath = await dialog.save({
            title: 'Save SVG',
            defaultPath: defaultSvgPath(),
            filters: [
                {
                    name: 'SVG Files',
                    extensions: ['svg']
                }
            ]
        });

        if (!savePath) return;
        await tauriInvoke('save_svg_file', {
            path: savePath,
            content: currentSvgContent
        });
    }

    async function convertWithTauri() {
        const smoothingMode = document.querySelector('input[name="smoothing"]:checked').value;
        const excludeWhite = document.getElementById('excludeWhite').checked;
        const excludeBlack = document.getElementById('excludeBlack').checked;

        updateProgress(12, 'Reading image locally...');
        await wait(120);
        updateProgress(42, 'Reducing colors with Rust K-Means...');

        const result = selectedFilePath
            ? await tauriInvoke('convert_image_quantized', {
                path: selectedFilePath,
                colors: Number(colorSlider.value),
                smoothing: smoothingMode,
                excludeWhite,
                excludeBlack
            })
            : await tauriInvoke('convert_image_placeholder', {
                fileName: selectedFile ? selectedFile.name : 'image',
                colors: Number(colorSlider.value),
                smoothing: smoothingMode,
                excludeWhite,
                excludeBlack
            });

        await wait(120);
        updateProgress(78, selectedFilePath ? 'Rendering quantized SVG preview...' : 'Rendering SVG preview...');
        await wait(120);
        updateProgress(100, 'Done');
        finishConversion(result);
    }

    // Handle desktop downloads.
    downloadBtn.addEventListener('click', async (e) => {
        if (isTauriDesktop()) {
            e.preventDefault();
            try {
                await saveSvgWithTauri();
            } catch (error) {
                console.error(error);
                const msg = translations[currentLang].errorMsg || "Error";
                alert(`${msg}: ${error.message}`);
            }
            return;
        }

        if (window.pywebview) {
            e.preventDefault();
            if (currentSvgContent) {
                const fname = selectedFile ? selectedFile.name : null;
                window.pywebview.api.save_svg(currentSvgContent, fname);
            }
        }
    });

    // Exit button handler
    if (exitBtn) {
        exitBtn.addEventListener('click', async () => {
            if (isTauriDesktop()) {
                await tauriInvoke('close_app');
            } else if (window.pywebview) {
                window.pywebview.api.close_app();
            }
        });
    }

    // Show Exit button if running in pywebview
    const showExitBtn = () => {
        if (exitBtn) exitBtn.classList.remove('hidden');
    };

    if (isTauriDesktop() || window.pywebview) {
        showExitBtn();
    } else {
        window.addEventListener('pywebviewready', showExitBtn);
    }

    // Handle File Selection
    imageInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            handleFileSelect(e.target.files[0], { path: null });
        }
    });

    // Intercept click on upload button for Desktop App
    const uploadButton = document.querySelector('.custom-file-upload');
    if (uploadButton) {
        uploadButton.addEventListener('click', (e) => {
            if (isTauriDesktop()) {
                e.preventDefault();
                e.stopPropagation();
                openImageWithTauri().catch(error => {
                    console.error(error);
                    const msg = translations[currentLang].errorMsg || "Error";
                    alert(`${msg}: ${error.message}`);
                });
            } else if (window.pywebview) {
                e.preventDefault();
                e.stopPropagation();
                
                window.pywebview.api.open_image().then(result => {
                    if (result) {
                        const file = fileFromBase64(result);
                        handleFileSelect(file, { path: null });
                    }
                });
            }
        });
    }

    function handleFileSelect(file, options = {}) {
        selectedFile = file;
        selectedFilePath = options.path || null;
        fileName.textContent = selectedFile.name;
        convertBtn.disabled = false;
        
        // Hide SVG/Download if exists
        downloadBtn.classList.add('disabled');
        // If it was hidden (old logic), ensure it's visible but disabled
        downloadBtn.classList.remove('hidden');
        paletteContainer.classList.add('hidden');

        // Preview Original
        const reader = new FileReader();
        reader.onload = (e) => {
            placeholderText.classList.add('hidden');
            imageContainer.innerHTML = `<img src="${e.target.result}" alt="Original">`;
        };
        reader.readAsDataURL(selectedFile);
    }

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
        downloadBtn.classList.add('disabled');
        
        // Reset Progress
        const progressBar = document.getElementById('progressBar');
        const progressPercentage = document.getElementById('progressPercentage');
        const loadingStatus = document.getElementById('loadingStatus');
        progressBar.style.width = '0%';
        progressPercentage.textContent = '0%';
        loadingStatus.textContent = translations[currentLang].processing;

        if (isTauriDesktop()) {
            try {
                await convertWithTauri();
            } catch (error) {
                console.error(error);
                const msg = translations[currentLang].errorMsg || "Error";
                alert(`${msg}: ${error.message}`);
                loading.classList.add('hidden');
                convertBtn.disabled = false;
            }
            return;
        }

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('colors', colorSlider.value);
        
        const smoothingMode = document.querySelector('input[name="smoothing"]:checked').value;
        formData.append('smoothing', smoothingMode);
        
        const excludeWhite = document.getElementById('excludeWhite').checked;
        const excludeBlack = document.getElementById('excludeBlack').checked;
        formData.append('excludeWhite', excludeWhite);
        formData.append('excludeBlack', excludeBlack);

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
        
        currentSvgContent = svgText;

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
        downloadBtn.classList.remove('disabled');

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
