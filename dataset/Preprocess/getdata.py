from pydub import AudioSegment
from pydub.silence import split_on_silence
import os
import io
import logging


def split(sound):
    dBFS = sound.dBFS
    return split_on_silence(
        sound, min_silence_len=100, silence_thresh=dBFS - 16, keep_silence=100
    )


def combine(_src):
    audio = AudioSegment.empty()
    for i, filename in enumerate(os.listdir(_src)):
        if filename.endswith(".flac"):
            filename = os.path.join(_src, filename)
            flac = AudioSegment.from_file(filename, format="flac")
            stream = io.BytesIO()
            flac.export(stream, format="wav")
            audio += flac
    return audio


def save_chunks(chunks, directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    counter = 0

    target_length = 5 * 1000
    output_chunks = [chunks[0]]
    for chunk in chunks[1:]:
        if len(output_chunks[-1]) < target_length:
            output_chunks[-1] += chunk
        else:
            # if the last output chunk is longer than the target length,
            # we can start a new one
            output_chunks.append(chunk)

    for chunk in output_chunks:
        chunk = chunk.set_frame_rate(24000)
        chunk = chunk.set_channels(1)
        counter = counter + 1
        chunk.export(os.path.join(directory, f"{str(counter)}.wav"), format="wav")


def save_chunks_speaker(spkr):
    print(spkr)
    # if not os.path.exists(directory):
    audio = combine(__CORPUSPATH__ + spkr)
    chunks = split(audio)
    save_chunks(chunks, __OUTPATH__ + spkr)


def save_chunks_speakers(spkrs):
    try:
        # num_cores = mp.cpu_count()
        # syn_ = partial(save_chunks_speaker)
        # results = Parallel(n_jobs=n_jobs, max_nbytes=None)(
        #     delayed(syn_)(spk) for spk in spkrs)
        for spk in spkrs:
            save_chunks_speaker(spk)
    except Exception as e:
        logging.error(e, exc_info=True)  # log stack trace
    return 0


"""
StarGAN v2
Copyright (c) 2020-present NAVER Corp.
This work is licensed under the Creative Commons Attribution-NonCommercial
4.0 International License. To view a copy of this license, visit
http://creativecommons.org/licenses/by-nc/4.0/ or send a letter to
Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.
"""


def generate_train_test_split():
    for spk in __SPEAKERS__:
        files = os.listdir(os.path.join(__OUTPATH__, spk))
        data_list = [
            os.path.join(__OUTPATH__, spk, file)
            for file in files
            if file.endswith(".wav")
        ]
        len_data_list = len(data_list)
        test_idx = int(0.1 * len_data_list)
        train_data = data_list[test_idx:]
        test_data = data_list[:test_idx]

        file_str = "".join(
            f"{item}|{int(__SPEAKERS__.index(spk))}" + "\n" for item in train_data
        )
        with open(f"{__OUTPATH__}/train_list.txt", "a") as text_file:
            text_file.write(file_str)
        file_str = "".join(
            f"{item}|{int(__SPEAKERS__.index(spk))}" + "\n" for item in test_data
        )
        with open(f"{__OUTPATH__}/val_list.txt", "a") as text_file:
            text_file.write(file_str)


def get_speakers():
    spkrs = os.listdir(__CORPUSPATH__)
    spkrs.sort()
    return spkrs


if __name__ == "__main__":
    # VCTK Corpus Path
    __CORPUSPATH__ = "/project/sughosh/dataset/wav48_silence_trimmed/"
    __OUTPATH__ = "/project/sughosh/dataset/VCTK-24k-All/"

    __SPEAKERS__ = get_speakers()
    # spkrs = [225, 228, 229, 230, 231, 233, 236, 239, 240, 244, 226, 227, 232, 243, 254, 256, 258, 259, 262, 272]
    # __SPEAKERS__ = [ 'p'+str(i) for i in spkrs]

    # downsample to 24 kHz and combine short utterance and save as one file
    save_chunks_speakers(__SPEAKERS__)
    generate_train_test_split()
