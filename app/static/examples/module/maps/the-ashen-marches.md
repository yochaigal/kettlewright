---
layout: default
id: map-0001
title: The Ashen Marches
type: Map
map_type: realm
---
Points, paths and drawing of this map. Edit the map in Kettlewright.

```kettlewright-map
{
  "article_id": "map-0001",
  "kind": "realm",
  "drawing": null,
  "nodes": [
    {"id": "point-0001", "article_id": "article-0001", "number": 1, "x": 180, "y": 240, "geometry": null, "nested_map": null},
    {"id": "point-0002", "article_id": "article-0003", "number": 2, "x": 620, "y": 180, "geometry": null, "nested_map": "article-0003"}
  ],
  "edges": [
    {"article_id": "article-0004", "source": "point-0001", "target": "point-0002"}
  ]
}
```
