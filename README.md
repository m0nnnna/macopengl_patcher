Hello!

I have setup a python script that is able to patch electron apps on macOS devices running Open Core Legacy Patcher.

You'll notice this scripts looks for some applications by default. I have only tested this with two.

1. Spotify
2. Discord

You'll see at the top of the script the applications you can add and modify, there are two choices script or patch.

Patch works for Discrod with 0 other mods.

Script works for Spotify and the patch does not.

For apps like Spotify once you run it it'll create a new launch wrapper inside of your user applications folder. Not the normal one.

```
'/Users/YOURUSER/Applications/Spotify OpenGL.app'
```
You can then add this to your dock or whatever else shortcut.
