# blender_import_n64_wrl
<p>Specifically designed to import "Nemu64 Graphics VRML (Lemmy's Video)" exports strait into blender 2.8+
<p><b>Use the ZIP file</b> to quickly install to Blender.
  <br>No need to unzip it.
  <br>Navigate to 'Edit > Preferences > Add-ons'. Use the install button here.

<h2>Importing</h2>
Blender Menus -> 'File > Import > N64 vrml (.wrl)'
<h2>CREDIT</h2>
<b>Nemu64 Graphics VRML (Lemmy's Video)</b>
Thanks to the dump that this person's plugin provides I was able to reassemble it in Blender.
<b>Project 64</b>
"Nemu64 Graphics" is a plugin for Project 64's emulator.

<h2>How to use</h2>
<ol>
  <li>You must have:
    <ul>
      <li>Project 64 v2.x+ installed.<br>
      <li>"Nemu64 Graphics (combine debug)" downloaded and placed in the "%project64%/Plugin/GFX" directory.<br>
      <li>Obviously you need to have your desired ROM (N64 Game).
    </ul>
  <li>This video will give you an idea about how to create a "N64 scene" dump.<br>
    https://www.youtube.com/watch?v=vz9dDyTTAGc<br>
    <i>His info will be outdated because of this plugin:</i>
    <ul>
      <li>Blender 2.8 or newer will be needed.
      <li>Version of Project 64 is not so important. As long as it accepts the "Nemu64 Graphics" plugin, it should work.
      <li>N64 Mapping tool is not required at all.
    </ul>
  <li>As soon as you have Textures and the .wrl file dumped in the "C://VRML" directory you can move on to Blender.
  <li>Blender Menus -> 'File > Import > N64 vrml (.wrl)'
  <li>Done
</ol>

<h2>Known Issue</h2>
Alpha transparency is somewhat implemented but not perfect.<br>
There was not enough data in the "Nemu64 Graphics" dump to be able to determine how to correctly handle alpha for each object. I did the best I could. Sadly, that meant I had to make the plugin a lot slower.<i>All Alpha files get scanned one by one. If they are completly black then I assumed that there is no alpha.</i><br>
Also some alphas are inverted. I could not determine which ones from the dump so instead I just made it easy to toggle.<br>
<b>To toggle the alpha</b> place a noodle from node output "Invert Alpha.value" to node input "Principled BSDF.Alpha".
