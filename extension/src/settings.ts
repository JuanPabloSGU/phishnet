document.addEventListener('DOMContentLoaded', () => {
    const toggleAutomaticSearch = document.getElementById('toggle-automatic-search') as HTMLInputElement;
    const saveSettings = document.getElementById('save-settings') as HTMLButtonElement;

    chrome.storage.local.get(['automatic_search'], (result) => {
        if (chrome.runtime.lastError) {
            console.error(chrome.runtime.lastError.message);
        } else {
            const automatic_search = result.automatic_search;
            toggleAutomaticSearch.checked = automatic_search !== undefined ? automatic_search : false; // Default to false
        }
    });

    saveSettings.addEventListener('click', () => {
        const isAutomaticSearch = toggleAutomaticSearch.checked;
        chrome.storage.local.set({ automatic_search: isAutomaticSearch }, () => {
            if (chrome.runtime.lastError) {
                console.error(chrome.runtime.lastError.message);
            }

            console.log('Automatic search setting saved:', isAutomaticSearch);
        });

        window.close();
    });
});
