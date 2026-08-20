export const MAX_SCREENSHOT_BYTES = 5 * 1024 * 1024;
export const SCREENSHOT_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/webp'];

export function validateScreenshotFile(file: File): string | null {
  if (!SCREENSHOT_TYPES.includes(file.type)) {
    return 'Use a PNG, JPG, GIF, or WebP image.';
  }
  if (file.size > MAX_SCREENSHOT_BYTES) {
    return 'Screenshot must be 5 MB or smaller.';
  }
  return null;
}

export function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(new Error('Could not read screenshot'));
    reader.readAsDataURL(file);
  });
}
