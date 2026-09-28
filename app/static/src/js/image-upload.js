// Compress before submitting the description; the server enforces the same limits.
export async function optimizeUpload(file) {
  if (!['image/png','image/jpeg','image/webp','image/gif'].includes(file.type) || file.size > 10*1024*1024) throw new Error('Invalid image');
  const image=await createImageBitmap(file, {imageOrientation:'from-image'});
  try {
    if (image.width*image.height > 25000000) throw new Error('Image too large');
    const canvas=document.createElement('canvas');
    let scale=Math.min(1,1600/Math.max(image.width,image.height));
    while (true) {
      canvas.width=Math.max(1,Math.round(image.width*scale));
      canvas.height=Math.max(1,Math.round(image.height*scale));
      canvas.getContext('2d').drawImage(image,0,0,canvas.width,canvas.height);
      for (const quality of [.82,.72,.62]) {
        const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/webp',quality));
        if (!blob || blob.type !== 'image/webp') throw new Error('WebP unavailable');
        if (blob.size <= 500*1024) {
          return await new Promise((resolve,reject)=>{
            const reader=new FileReader(); reader.onload=()=>resolve(reader.result); reader.onerror=reject; reader.readAsDataURL(blob);
          });
        }
      }
      scale*=.8;
    }
  } finally {image.close();}
}
