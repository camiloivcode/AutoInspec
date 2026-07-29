const MAX_WIDTH = 1920
const MAX_HEIGHT = 1920
const QUALITY = 0.85
const OUTPUT_FORMAT = 'image/jpeg'

export async function compressImage(file: File): Promise<File> {
  if (!file.type.startsWith('image/')) return file

  const img = await createImageBitmap(file)
  let { width, height } = img

  if (width <= MAX_WIDTH && height <= MAX_HEIGHT && file.type === OUTPUT_FORMAT) {
    img.close()
    return file
  }

  if (width > MAX_WIDTH) {
    height = Math.round((height * MAX_WIDTH) / width)
    width = MAX_WIDTH
  }
  if (height > MAX_HEIGHT) {
    width = Math.round((width * MAX_HEIGHT) / height)
    height = MAX_HEIGHT
  }

  const canvas = new OffscreenCanvas(width, height)
  const ctx = canvas.getContext('2d')!
  ctx.drawImage(img, 0, 0, width, height)
  img.close()

  const blob = await canvas.convertToBlob({ type: OUTPUT_FORMAT, quality: QUALITY })
  const ext = OUTPUT_FORMAT === 'image/jpeg' ? '.jpg' : '.png'
  const name = file.name.replace(/\.[^.]+$/, '') + ext

  return new File([blob], name, { type: OUTPUT_FORMAT })
}
