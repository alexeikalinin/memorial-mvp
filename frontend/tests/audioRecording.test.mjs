import test from 'node:test'
import assert from 'node:assert/strict'
import { createAudioRecorder, recordingBlob, recordingFile, releaseRecorder } from '../src/utils/audioRecording.js'
import { getVisitorId } from '../src/utils/visitorIdentity.js'

test('Safari MP4 recording keeps its real format and releases microphone', () => {
  let stopped = 0
  const stream = { getTracks: () => [{ stop: () => stopped++ }] }
  globalThis.MediaRecorder = class {
    static isTypeSupported(type) { return type === 'audio/mp4' }
    constructor(stream, options) { this.stream = stream; this.mimeType = options.mimeType; this.state = 'recording' }
    stop() { this.state = 'inactive' }
  }
  const recorder = createAudioRecorder(stream)
  assert.equal(recorder.mimeType, 'audio/mp4')
  const file = recordingFile(recordingBlob([new Blob(['audio'], { type: 'audio/mp4' })], recorder))
  assert.equal(file.name, 'recording.mp4')
  assert.equal(file.type, 'audio/mp4')
  releaseRecorder(recorder)
  assert.equal(stopped, 1)
  assert.equal(recorder.state, 'inactive')
  delete globalThis.MediaRecorder
})

test('restricted browser storage still permits stable visitor identity', () => {
  globalThis.localStorage = { getItem() { throw Error('blocked') }, setItem() { throw Error('blocked') } }
  const id = getVisitorId('restricted-test')
  assert.match(id, /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/)
  assert.equal(getVisitorId('restricted-test'), id)
  delete globalThis.localStorage
})
