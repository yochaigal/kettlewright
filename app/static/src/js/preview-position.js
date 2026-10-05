// Keep the source link outside the panel, including after a map preview grows.
export function previewPosition(link, width, height, viewportWidth, viewportHeight) {
  const margin=8, gap=6;
  const left=Math.max(margin, Math.min(link.left, viewportWidth-width-margin));
  const top=Math.max(margin, Math.min(link.top, viewportHeight-height-margin));
  const below=viewportHeight-link.bottom-gap-margin, above=link.top-gap-margin;
  if(height<=below) return {left,top:link.bottom+gap,maxHeight:below};
  if(height<=above) return {left,top:link.top-gap-height,maxHeight:above};
  if(link.right+gap+width<=viewportWidth-margin)
    return {left:link.right+gap,top,maxHeight:viewportHeight-2*margin};
  if(link.left-gap-width>=margin)
    return {left:link.left-gap-width,top,maxHeight:viewportHeight-2*margin};
  // On narrow screens, use the larger vertical space and scroll the contents.
  return below>=above
    ? {left,top:link.bottom+gap,maxHeight:below}
    : {left,top:margin,maxHeight:above};
}
