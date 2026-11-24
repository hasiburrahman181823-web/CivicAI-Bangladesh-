const photoTypes = ['image/jpeg', 'image/png', 'image/webp'];
const videoTypes = ['video/mp4', 'video/quicktime', 'video/webm'];
const megabyte = 1024 * 1024;

export const evidenceAccept = [...photoTypes, ...videoTypes, '.jpg', '.jpeg', '.png', '.webp', '.mp4', '.mov', '.webm'].join(',');

export function validEvidence(file) {
  const video = videoTypes.includes(file.type) || /\.(mp4|mov|webm)$/i.test(file.name);
  const photo = photoTypes.includes(file.type) || /\.(jpe?g|png|webp)$/i.test(file.name);
  return (video || photo) && file.size > 0 && file.size <= (video ? 12 : 2) * megabyte;
}
