<script>
  import { onMount } from 'svelte';
  
  let ws;
  onMount(() => {
    ws = new WebSocket(`ws://${location.host}/ws`);
    
    ws.onmessage = (event) => {
      // Handle ComfyUI messages
    };
  });
</script>

<div class="p-4">
    <h1 class="text-4xl font-bold text-primary">My ComfyUI Addon</h1>
    <div class="card bg-base-200 shadow-xl mt-4">
      <div class="card-body">
        <h2 class="card-title">Control Panel</h2>
        <button class="btn btn-primary">Generate</button>
      </div>
    </div>
  </div>