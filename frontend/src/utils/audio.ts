export async function convertWebmToWav(webmBlob: Blob): Promise<Blob> {
  const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext
  const audioContext = new AudioContextClass({ sampleRate: 16000 })
  try {
    const arrayBuffer = await webmBlob.arrayBuffer()
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)
    const wav = audioBufferToWav(audioBuffer)
    return new Blob([wav], { type: 'audio/wav' })
  } finally {
    await audioContext.close().catch(() => undefined)
  }
}

function audioBufferToWav(buffer: AudioBuffer): ArrayBuffer {
  const numChannels = 1
  const sampleRate = buffer.sampleRate
  const bytesPerSample = 2
  const blockAlign = numChannels * bytesPerSample
  const data = buffer.getChannelData(0)
  const dataLength = data.length * bytesPerSample
  const arrayBuffer = new ArrayBuffer(44 + dataLength)
  const view = new DataView(arrayBuffer)

  writeString(view, 0, 'RIFF')
  view.setUint32(4, 36 + dataLength, true)
  writeString(view, 8, 'WAVE')
  writeString(view, 12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, numChannels, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * blockAlign, true)
  view.setUint16(32, blockAlign, true)
  view.setUint16(34, 16, true)
  writeString(view, 36, 'data')
  view.setUint32(40, dataLength, true)
  floatTo16BitPcm(view, 44, data)

  return arrayBuffer
}

function writeString(view: DataView, offset: number, value: string) {
  for (let index = 0; index < value.length; index += 1) {
    view.setUint8(offset + index, value.charCodeAt(index))
  }
}

function floatTo16BitPcm(view: DataView, offset: number, input: Float32Array) {
  for (let index = 0; index < input.length; index += 1, offset += 2) {
    const sample = Math.max(-1, Math.min(1, input[index] ?? 0))
    view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true)
  }
}

export async function blobToBase64(blob: Blob): Promise<string> {
  const buffer = await blob.arrayBuffer()
  let binary = ''
  const bytes = new Uint8Array(buffer)
  const chunkSize = 0x8000
  for (let index = 0; index < bytes.length; index += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(index, index + chunkSize))
  }
  return btoa(binary)
}
