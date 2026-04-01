"""
Configuration management via environment variables with safe defaults.
"""

import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")

    # Upload limits
    MAX_FILES = int(os.getenv("MAX_FILES", 20))
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 100))
    MAX_CONTENT_LENGTH = MAX_FILE_SIZE_MB * 1024 * 1024

    # Storage
    UPLOAD_BASE_DIR = os.getenv("UPLOAD_BASE_DIR", "/tmp/metadata_cleaner_uploads")
    SESSION_TTL_MINUTES = int(os.getenv("SESSION_TTL_MINUTES", 30))

    # Branding
    PAGE_TITLE = os.getenv("PAGE_TITLE", "Metadata Cleaner")
    SUPPORT_MESSAGE = os.getenv("SUPPORT_MESSAGE", "For support, contact your IT department.")

    # ExifTool
    EXIFTOOL_PATH = os.getenv("EXIFTOOL_PATH", None)  # None = auto-detect from PATH

    ALLOWED_EXTENSIONS = {
        "3g2", "3gp2", "3gp", "3gpp", "aax", "ai", "ait", "arq", "arw",
        "avif", "cr2", "cr3", "crm", "crw", "ciff", "cs1", "dcp", "dng",
        "dr4", "dvb", "eps", "epsf", "ps", "erf", "exif", "exv", "f4a",
        "f4b", "f4p", "f4v", "fff", "flif", "gif", "glv", "gpr", "hdp",
        "wdp", "jxr", "heic", "heif", "hif", "icc", "icm", "iiq", "ind",
        "indd", "indt", "insp", "jp2", "jpf", "jpm", "jpeg", "jpg", "jpe",
        "jxl", "lrv", "m4a", "m4b", "m4p", "m4v", "mef", "mie", "mos",
        "mov", "qt", "mp4", "mpo", "mqv", "mrw", "nef", "nksc", "nrw",
        "orf", "ori", "pdf", "pef", "png", "jng", "mng", "ppm", "pbm",
        "pgm", "psd", "psb", "psdt", "qtif", "qti", "qif", "raf", "raw",
        "rw2", "rwl", "sr2", "srw", "thm", "tiff", "tif", "vrd", "webp",
        "x3f", "xmp",
    }

    # Metadata fields that are technical/non-sensitive and excluded from the preview
    EXCLUDED_METADATA_FIELDS = {
        "Directory", "ExifToolVersion", "FileAccessDate", "FileInodeChangeDate",
        "FileModifyDate", "FileName", "FilePermissions", "FileSize", "FileType",
        "FileTypeExtension", "Linearized", "MIMEType", "PDFVersion", "PageCount",
        "SourceFile", "BitDepth", "ColorType", "Compression", "Filter", "ImageSize",
        "ImageWidth", "Interlace", "Megapixels", "AudioBitsPerSample", "AudioChannels",
        "AudioFormat", "AudioSampleRate", "AvgBitrate", "Balance", "CompatibleBrands",
        "CompressorID", "CurrentTime", "Duration", "GraphicsMode", "HandlerType",
        "ImageHeight", "MajorBrand", "MatrixStructure", "MediaCreateDate",
        "MediaDataOffset", "MediaDataSize", "MediaDuration", "MediaHeaderVersion",
        "MediaLanguageCode", "MediaModifyDate", "MediaTimeScale", "MinorVersion",
        "MovieHeaderVersion", "NextTrackID", "OpColor", "PosterTime",
        "PreferredRate", "PreferredVolume", "PreviewDuration", "PreviewTime",
        "Rotation", "SelectionDuration", "SelectionTime", "SourceImageHeight",
        "SourceImageWidth", "TimeScale", "TrackCreateDate", "TrackDuration",
        "TrackHeaderVersion", "TrackID", "TrackLayer", "TrackModifyDate",
        "TrackVolume", "VideoFrameRate", "XResolution", "YResolution",
        "BlueX", "BlueY", "GreenX", "GreenY", "RedX", "RedY", "WhitePointX", "WhitePointY",
        "Language", "TaggedPDF", "APP14Flags0", "APP14Flags1", "BitsPerSample",
        "ColorComponents", "ColorTransform", "DCTEncodeVersion", "EncodingProcess",
        "YCbCrSubSampling",
    }

    # Cleaning presets: maps preset name to exiftool flags
    CLEANING_PRESETS = {
        "full": ["-all=", "-ICC_Profile:all=", "-XMP:all=", "-IPTC:all="],
        "safe": ["-GPS:all=", "-Author=", "-Creator=", "-Artist=", "-Copyright=",
                 "-SerialNumber=", "-CameraSerialNumber=", "-OwnerName=",
                 "-XMP:Creator=", "-XMP:Rights=", "-IPTC:By-line="],
        "privacy": ["-GPS:all=", "-Author=", "-Creator=", "-Artist=",
                    "-SerialNumber=", "-CameraSerialNumber=", "-OwnerName=",
                    "-Comment=", "-UserComment=", "-XPComment=",
                    "-XMP:Creator=", "-IPTC:By-line=", "-Software="],
    }

    # Fields considered high-sensitivity for the risk indicator
    HIGH_SENSITIVITY_FIELDS = {
        "GPSLatitude", "GPSLongitude", "GPSAltitude", "GPSPosition",
        "Author", "Creator", "Artist", "OwnerName", "SerialNumber",
        "CameraSerialNumber", "LensSerialNumber", "InternalSerialNumber",
        "Comment", "UserComment", "XPComment", "Software",
        "MakerNote", "SpecialInstructions",
    }
