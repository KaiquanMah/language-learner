from google.colab import userdata
GOOGLE_API_KEY=userdata.get('GOOGLE_API_KEY')


# @title Install stuff, monkey patch old Python {display-mode: 'form'}
%pip install -q websockets taskgroup

# Colab runs Python 3.11, but this needs a backport of taskgroup
# monkey patch:
import asyncio, taskgroup, exceptiongroup
asyncio.TaskGroup = taskgroup.TaskGroup
asyncio.ExceptionGroup = exceptiongroup.ExceptionGroup



#################################### 
# Inline copy of colab_stream
####################################
# @title Inline copy of colab_stream {display-mode: 'form'}
import asyncio, contextlib, json
from google.colab import output
from IPython import display

# alt:
# message.WaitForRawInput()
# colab.frontend.sendMessage({'action': 'keyboard_input', 'payload': state.send});

_start_session_js = """
let start_session = (userFn) => {
  let debug = console.log;
  debug = ()=>{};

  let ctrl = new AbortController();
  let state = {
    recv: [],
    onRecv: () => {},
    send: [],
    onDone: new Promise((acc) => ctrl.signal.addEventListener('abort', () => acc())),
    write: (data) => {
      state.send.push(data);
    }
  };
  window._js_session_on_poll = (data) => {
    debug("on_poll", data);
    for (let msg of data) {
      if ('data' in msg) {
        state.recv.push(msg.data);
      }
      if ('error' in msg) {
        ctrl.abort(new Error('Remote: ' + msg.error));
      }
      if ('finish' in msg) {
        // TODO
        ctrl.abort(new Error('Remote: finished'));
      }
    }
    state.onRecv();
    let result = state.send;
    state.send = [];
    debug("on_poll: result", result);
    return result;
  };
  let connection = {
    signal: ctrl.signal,
    read: async () => {
      while(!ctrl.signal.aborted) {
        if (state.recv.length != 0) {
          return state.recv.shift();
        }
        await Promise.race([
          new Promise((acc) => state.onRecv = acc),
          state.onDone,
        ]);
      }
    },
    write: (data) => {
      state.write({'data': data});
    }
  };
  debug("starting userFn");
  userFn(connection).then(() => {
    debug("userFn finished");
    ctrl.abort(new Error("end of input"));
    state.write({'finished': true});
  },
  (e) => {
    debug("userFn error", e);
    console.error("Stream function failed", e);
    ctrl.abort(e);
    state.write({'error': '' + e});
  });
};
"""


class Connection:

  def __init__(self):
    self._recv = []
    self._on_recv_ready = asyncio.Event()
    self._send = []
    self._on_done = asyncio.Future()

  async def write(self, data):
    self._send.append({'data': data})

  async def read(self):
    while not self._on_done.done() and not self._recv:
      self._on_recv_ready.clear()
      await self._on_recv_ready.wait()
    # print("read, done waiting: ", self._recv, self._on_done)
    if self._on_done.done() and self._on_done.exception() is not None:
      raise self._on_done.exception()
    elif self._recv:
      return self._recv.pop(0)
    else:
      return EOFError('End of stream')

  def _poll(self):
    # Polling is needed as ipykernel has blocking mainloop
    # (Comms do not work)
    # print("calling poll")
    res = output.eval_js(f'window._js_session_on_poll({json.dumps(self._send)})')
    # print("poll: ", res)
    self._send = []
    for r in res:
      if 'data' in r:
        self._recv.append(r['data'])
        self._on_recv_ready.set()
      elif 'error' in r:
        self._on_done.set_exception(Exception('Remote error: ' + r['error']))
        self._on_recv_ready.set()
      elif 'finished' in r:
        self._on_done.set_result(None)
        self._on_recv_ready.set()

  async def _pump(self, pump_interval):
    while not self._on_done.done():
      self._poll()
      await asyncio.sleep(pump_interval)


@contextlib.asynccontextmanager
async def RunningLiveJs(userCode, pump_interval=0.1):
  """Runs given javascript async code connecting it to colab.

  Use .write(msg) and .read() methods on this context manager
  to exchange messages with JavaScript code.

  From JavaScript use 'connection.write(data)'
  and 'await connection.read()' to exchange messages with colab.
  """
  c = Connection()
  output.eval_js(
      f"""
    let userFn = async (connection) => {{
      {userCode}
    }};
    {_start_session_js};
    start_session(userFn);
    1;
  """,
      ignore_result=True
  )
  t = asyncio.create_task(c._pump(pump_interval))

  def log_error(f):
    if f.exception() is not None:
      print('error: ', f.exception())

  t.add_done_callback(log_error)
  try:
    yield c
  finally:
    t.cancel()
    output.eval_js(
        """window._js_session_on_poll([{finish: true}]);""", ignore_result=True
    )
####################################















####################################
# @title Inline copy of colab_audio {display-mode: 'form'}
####################################
"""Realtime Audio I/O support.

Example use:

  async with colab_audio.RunningLiveAudio() as audio:
    bytes_per_second = audio.config.sample_rate * audio.config.frame_size
    print ('recording (3sec)')
    buf = b''
    while len(buf) < 3*bytes_per_second:
      buf += await audio.read()
    print ('playing')
    await audio.enqueue(buf)
    await asyncio.sleep(3)
    print ('done')
    display.display(colab_audio.Audio(audio.config, buf))
"""

import asyncio
import base64
from collections.abc import AsyncIterator
import contextlib
import dataclasses
import io
import json
import time
import wave
import numpy as np


@dataclasses.dataclass(frozen=True)
class AudioConfig:
  """Configuration of audio stream."""

  sample_rate: int
  format: str = 'S16_LE'  # only supported value
  channels: int = 1  # only supported value

  @property
  def sample_size(self) -> int:
    assert self.format == 'S16_LE'
    return 2

  @property
  def frame_size(self) -> int:
    return self.channels * self.sample_size

  @property
  def numpy_dtype(self) -> np.dtype:
    assert self.format == 'S16_LE'
    return np.dtype(np.int16).newbyteorder('<')


@dataclasses.dataclass(frozen=True)
class Audio:
  """Unit of audio data with configuration."""

  config: AudioConfig
  data: bytes

  @staticmethod
  def silence(config: AudioConfig, length_seconds: float | int) -> 'Audio':
    frame = b'\0' * config.frame_size
    num_frames = int(length_seconds * config.sample_rate)
    if num_frames < 0:
      num_frames = 0
    return Audio(config=config, data=frame * num_frames)

  def as_numpy(self):
    return np.frombuffer(self.data, dtype=self.config.numpy_dtype)

  def as_wav_bytes(self) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, 'w') as wav:
      wav.setnchannels(self.config.channels)
      wav.setframerate(self.config.sample_rate)
      assert self.config.format == 'S16_LE'
      wav.setsampwidth(2)  # 16bit
      wav.writeframes(self.data)
    return buf.getvalue()

  def _ipython_display_(self):
    """Hook displaying audio as HTML tag."""
    from IPython.display import display, HTML

    b64_wav = base64.b64encode(self.as_wav_bytes()).decode('utf-8')
    display(HTML(f"""
        <audio controls>
          <source src="data:audio/wav;base64,{b64_wav}">
        </audio>
    """.strip()))

  async def astream_realtime(
      self, expected_delta_sec: float = 0.1
  ) -> AsyncIterator[bytes]:
    """Yields audio data in chunks as if it was played realtime."""
    current_pos = 0
    mono_start_ns = time.monotonic_ns()
    while current_pos < len(self.data):
      # print('sleep')
      await asyncio.sleep(expected_delta_sec)
      delta_ns = time.monotonic_ns() - mono_start_ns
      expected_pos_frames = int(delta_ns * self.config.sample_rate / 1e9)
      next_pos = expected_pos_frames * self.config.frame_size
      # print (f'{next_pos = }, {current_pos =}, {len(self.data) = }')
      if next_pos > current_pos:
        yield self.data[current_pos:next_pos]
        current_pos = next_pos

  def __add__(self, other: 'Audio') -> 'Audio':
    assert self.config == other.config
    return Audio(config=self.config, data=self.data + other.data)


class FailedToStartError(Exception):
  """Raised when audio session fails to start."""


class AudioSession:
  """Connection to audio recording/playback on client side."""

  def __init__(self, config: AudioConfig, connection: Connection):
    self._config = config
    self._connection = connection
    self._done = False
    self._read_queue: asyncio.Queue[bytes] = asyncio.Queue()
    self._started = asyncio.Future()

  @property
  def config(self) -> AudioConfig:
    return self._config

  async def await_start(self):
    await self._started

  async def _read_loop(self):
    # print ('read_loop')
    while True:
      # print ('await read')
      data = await self._connection.read()
      # print("data", data)
      if 'audio_in' in data:
        # print("audio_in", data['audio_in'])
        raw_data = base64.b64decode(data['audio_in'].encode('utf-8'))
        # print("audio_in", raw_data)
        self._read_queue.put_nowait(raw_data)
      if 'started' in data:
        self._started.set_result(None)
      if 'failed_to_start' in data:
        self._started.set_exception(
            FailedToStartError(
                f'Failed to start audio: {data["failed_to_start"]}'
            )
        )

  async def enqueue(self, audio_data: bytes):
    b64_data = base64.b64encode(audio_data).decode('utf-8')
    await self._connection.write({'audio_out': b64_data})

  async def clear_queue(self):
    await self._connection.write({'flush': True})

  async def read(self) -> bytes:
    return await self._read_queue.get()


STANDARD_AUDIO_CONFIG = AudioConfig(sample_rate=16000, channels=1)


# JavaScript code running in AudioWorklet, executing realtime audio processing.
_audio_processor_worklet_js = """
class PortProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this._queue = [];
    this.port.onmessage = (event) => {
      //console.log(event.data);
      if ('enqueue' in event.data) {
        this.enqueueAudio(event.data.enqueue);
      }
      if ('clear' in event.data) {
        this.clearAudio();
      }
    };
    this._out = [];
    this._out_len = 0;
    console.log("PortProcessor ctor", this);

    this.port.postMessage({
      debug: "Hello from the processor!",
    });
  }

  encodeAudio(input) {
    const channel = input[0];
    const data = new ArrayBuffer(2 * channel.length);
    const view = new DataView(data);
    for (let i=0; i<channel.length; i++) {
      view.setInt16(2*i, channel[i] * 32767, true);
    }
    return data;
  }

  enqueueAudio(input) { // bytearray
    let view = new DataView(input);
    let floats = [];
    for (let i=0; i<input.byteLength; i+=2) {
      floats.push(view.getInt16(i, true) / 32768.0);
    }
    this._queue.push(Float32Array.from(floats));
  }

  dequeueIntoBuffer(output) { // Float32Array
    //console.log('deq', output)
    let idx = 0;
    while (idx < output.length) {
      if (this._queue.length === 0) {
        return;
      }
      let input = this._queue[0];
      if (input.length == 0) {
        this._queue.shift();
        continue;
      }
      let n = Math.min(input.length, output.length - idx);
      output.set(input.subarray(0, n), idx);
      this._queue[0] = input.subarray(n);
      idx += n;
    }
  }

  clearAudio() {
    this._queue = [];
  }

  process(inputs, outputs, parameters) {
    // forward input audio
    let data = this.encodeAudio(inputs[0]);
    this._out.push(data);
    this._out_len += data.byteLength;
    // only send in 50ms batches, ipykernel will die when it gets too frequent
    if (this._out_len > (2*sampleRate / 20)) {
      let concat = new Uint8Array(this._out_len);
      let idx = 0;
      for (let a of this._out) {
        concat.set(new Uint8Array(a), idx);
        idx += a.byteLength;
      }
      this._out = [];
      this._out_len = 0;
      this.port.postMessage({
        'audio_in': concat.buffer,
      });
    }

    // forward output
    this.dequeueIntoBuffer(outputs[0][0]);
    // copy to other channels
    for (let i=1; i<outputs[0].length; i++) {
      const src = outputs[0][0];
      const dst = outputs[0][i];
      dst.set(src.subarray(0, dst.length));
    }
    return true;
  }
}

registerProcessor('port-processor', PortProcessor);
"""

# JavaScript code running in Colab UI IFrame.
_audio_session_js = """
let audioCtx = new AudioContext({sampleRate: sample_rate});
await audioCtx.audioWorklet.addModule(URL.createObjectURL(
  new Blob([audio_worklet_js], {type: 'text/javascript'})
));
let userMedia;
try {
  userMedia = await navigator.mediaDevices.getUserMedia({
    audio: {sampleRate: sample_rate, echoCancellation: true, channelCount: 1},
  });
} catch (e) {
  connection.write({failed_to_start: e});
  throw e;
}
console.log("colab_audio: userMedia=", userMedia);
connection.write({started: true})
//await userMedia.getAudioTracks()[0].applyConstraints({channelCount: 1});

try {
  let source = audioCtx.createMediaStreamSource(userMedia);
  let processor = new AudioWorkletNode(audioCtx, 'port-processor');
  processor.port.onmessage = (event) => {
    if ('audio_in' in event.data) {
      // base64 encode ugly way
      let encoded = btoa(String.fromCharCode(
          ...Array.from(new Uint8Array(event.data.audio_in))));
      //console.log("base64 input", encoded);
      connection.write({audio_in: encoded});
    } else {
      console.log("from processor (unhandled)", event);
    }
  };
  source.connect(processor);
  processor.connect(audioCtx.destination);
  //await new Promise((acc) => setTimeout(acc, 1000));
  while(!connection.signal.aborted) {
    let request = await connection.read();
    //console.log(request);
    if ('audio_out' in request) {
      let decoded = Uint8Array.from(
          atob(request.audio_out), c => c.charCodeAt(0)).buffer;
      //console.log('Enqueue', decoded);
      processor.port.postMessage({'enqueue': decoded});
    } else if('flush' in request) {
      processor.port.postMessage({'clear': ''});
    }
  }
} finally {
  userMedia.getTracks().forEach(t => t.stop());
  audioCtx.close();
}
"""


@contextlib.asynccontextmanager
async def RunningLiveAudio(
    config: AudioConfig = STANDARD_AUDIO_CONFIG, pump_interval=0.1
):
  """Runs audio connection to Colab UI and returns `AudioConnection` connected to it."""
  assert config.channels == 1
  assert config.format == 'S16_LE'
  required_js = f"""
    const audio_worklet_js = {json.dumps(_audio_processor_worklet_js)};
    const sample_rate = {json.dumps(config.sample_rate)};
    {_audio_session_js}
  """
  try:
    async with contextlib.AsyncExitStack() as stack:
      tg = await stack.enter_async_context(asyncio.TaskGroup())
      connection = await stack.enter_async_context(
          RunningLiveJs(required_js, pump_interval)
      )
      session = AudioSession(config, connection)
      read_task = tg.create_task(session._read_loop())  # copy data to queue
      tg.create_task(session.await_start())  # fail session if it fails to start
      yield session
      read_task.cancel()
  except asyncio.ExceptionGroup as e:
    if len(e.exceptions) == 1:
      raise e.exceptions[0]
    else:
      raise
####################################








####################################
# Client implementation
####################################

# @title Client implementation {display-mode: 'form'}
# @markdown This cell runs client connection to BidiGenerate with realtime audio I/O
from websockets.asyncio.client import connect
import asyncio
import contextlib
import base64
import json


HOST = 'generativelanguage.googleapis.com' # @param {type:'string'}
from google.colab import userdata
GOOGLE_API_KEY = userdata.get('GOOGLE_API_KEY')
API_KEY = GOOGLE_API_KEY
MODEL = 'models/gemini-live-2.5-flash-preview' # @param {type:'string'}
INITIAL_REQUEST_TEXT = "You are a helpful translation chatbot. Help beginners learn how to pronounce a word they say in the native language in Hebrew." # @param {type:'string'}


def encode_audio_input(data: bytes, config: AudioConfig) -> dict:
  """Build JSPB message with user input audio bytes."""
  return {
      'realtimeInput': {
          'mediaChunks': [{
              'mimeType': f'audio/pcm;rate={config.sample_rate}',
              'data': base64.b64encode(data).decode('UTF-8'),
          }],
      },
  }


def encode_text_input(text: str) -> dict:
  """Builds JSPB message with user input text."""
  return {
      'clientContent': {
          'turns': [{
              'role': 'USER',
              'parts': [{'text': text}],
          }],
          'turnComplete': True,
      },
  }


def decode_audio_output(input: dict) -> bytes:
  """Returns byte string with model output audio."""
  result = []
  content_input = input.get('serverContent', {})
  content = content_input.get('modelTurn', {})
  for part in content.get('parts', []):
    data = part.get('inlineData', {}).get('data', '')
    if data:
      result.append(base64.b64decode(data))
  return b''.join(result)


async def main():
  async with contextlib.AsyncExitStack() as es:
    tg = await es.enter_async_context(asyncio.TaskGroup())
    audio = await es.enter_async_context(RunningLiveAudio(AudioConfig(sample_rate=24000)))
    conn = await es.enter_async_context(connect(f'wss://{HOST}/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key={API_KEY}'))
    print('<connected>')

    initial_request = {
        'setup': {
            'model': MODEL,
        },
    }
    await conn.send(json.dumps(initial_request))

    if text := INITIAL_REQUEST_TEXT:
      await conn.send(json.dumps(encode_text_input(text)))

    async def send_audio():
      while True:
        data = await audio.read()
        await conn.send(json.dumps(encode_audio_input(data, audio.config)))

    tg.create_task(send_audio())
    enqueued_audio = []
    async for msg in conn:
      msg = json.loads(msg)
      if to_play := decode_audio_output(msg):
        enqueued_audio.append(to_play)
        await audio.enqueue(to_play)  # enqueue TTS
      elif 'interrupted' in msg.get('serverContent', {}):
        print('<interrupted by the user>')
        await audio.clear_queue()  # stop TTS
      elif 'turnComplete' in msg.get('serverContent', {}):
        if enqueued_audio:  # display it for later playback
          display.display(Audio(config=audio.config, data=b''.join(enqueued_audio)))
        enqueued_audio = []
        print('<end of turn>')
      else:
        if msg != {'serverContent': {}}:
          print(f'unhandled message: {msg}')

try:
  await main()
except asyncio.ExceptionGroup as e:
  raise e.exceptions[0]




####################################

