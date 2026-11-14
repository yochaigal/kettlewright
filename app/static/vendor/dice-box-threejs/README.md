# dice-box-threejs

[@3d-dice/dice-box-threejs](https://github.com/3d-dice/dice-box-threejs) 0.0.12 (MIT, see `LICENSE`),
the `dist/dice-box-threejs.es.js` file from its npm package (three.js and cannon-es are bundled in).

Used by `src/js/dice3d.js` to animate dice that land on the values the server rolled
(`box.roll('2d6@3,5')`). Loaded the first time someone rolls with 3D dice enabled.
No textures or sounds are used, so none of the package's `public/` assets are needed.
