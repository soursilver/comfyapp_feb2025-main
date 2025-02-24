<script>
  import { onMount } from "svelte";
  import MainForm from "./MainForm.svelte";
  import Settings from "./Settings.svelte";

  // defaults
  let serverAddress = "http://127.0.0.1:8188";
  let useCkptModels = false;
  let positivePrompt = "Hyperrealistic image of futuristic futuristic scene, realistic style";
  let selectedModel = "";
  let showSettings = false;
  let selectedSize = "1024x1024";
  let steps = 25;
  let cfg = 3.5;
  let loaded = false; // loading state

  onMount(() => {
    const savedSettings = localStorage.getItem('appSettings');
    if (savedSettings) {
      try {
        const settings = JSON.parse(savedSettings);
        // Update all state at once
        serverAddress = settings.serverAddress || serverAddress;
        useCkptModels = settings.useCkptModels ?? useCkptModels;
        positivePrompt = settings.positivePrompt || positivePrompt;
        selectedModel = settings.selectedModel || selectedModel;
        selectedSize = settings.selectedSize || selectedSize;
        steps = settings.steps || steps;
        cfg = settings.cfg || cfg;
      } catch (e) {
        console.error('Error loading settings:', e);
      }
    }
    loaded = true; // Mark initialization complete
  });

  function toggleSettings() {
    showSettings = !showSettings;
  }

  function handleSave(event) {
    // Save logic remains the same
    serverAddress = event.detail.address;
    useCkptModels = event.detail.useCkpt;
    
    const settings = {
      serverAddress,
      useCkptModels,
      positivePrompt,
      selectedModel,
      selectedSize,
      steps,
      cfg
    };
    localStorage.setItem('appSettings', JSON.stringify(settings));
    
    showSettings = false;
  }
</script>

<div class="container">
  <main class="px-4 py-6">
    <nav>
      <button on:click={toggleSettings} class="btn btn-outline mr-2">
        Settings
      </button>
    </nav>
    {#if showSettings}
      <div class="fixed inset-0 bg-black/50 z-10"></div>
      <Settings
        on:save={handleSave}
        currentAddress={serverAddress}
        useCkptModels={useCkptModels}
        className="z-20"
      />
    {/if}
    
    {#if loaded}
      <MainForm 
        bind:serverAddress 
        bind:useCkptModels 
        bind:positivePrompt
        bind:selectedModel
        bind:selectedSize
        bind:steps
        bind:cfg
        key={serverAddress + useCkptModels}
      />
    {/if}
  </main>
</div>