export function createAudioRecorder(stream) {
  try {
    if (typeof MediaRecorder === 'undefined') throw new Error('Audio recording is unavailable in this browser')
    const mimeType = ['audio/webm;codecs=opus', 'audio/mp4', 'audio/webm'].find(type => MediaRecorder.isTypeSupported(type))
    return mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream)
  } catch (error) {
    stream.getTracks().forEach(track => track.stop())
    throw error
  }
}
export function recordingBlob(chunks, recorder) {
  return new Blob(chunks, { type: recorder.mimeType || chunks.find(chunk => chunk.type)?.type || 'audio/webm' })
}
export function recordingFile(blob, name = 'recording') {
  const type = blob.type || 'audio/webm'
  const extension = type.includes('mp4') ? 'mp4' : type.includes('mpeg') ? 'mp3' : type.includes('wav') ? 'wav' : type.includes('ogg') ? 'ogg' : 'webm'
  return new File([blob], `${name}.${extension}`, { type })
}
export function releaseRecorder(recorder) {
  if (!recorder) return
  recorder.onstop = null
  if (recorder.state !== 'inactive') recorder.stop()
  recorder.stream.getTracks().forEach(track => track.stop())
}
