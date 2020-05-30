import re
from enum import Enum

"""
Modified Semver 2.0 spec Regex https://semver.org/
Template: <major>.<minor>.<patch>.<build>-<prerelease>+<buildmetadata>
How they differ from spec:    
    major: required (no changes)
    minor: optional (required in spec)
    patch: optional (required in spec)
    build: optional (not allowed in spec)
    prerelease: optional (no changes)
    buildmetadata: optional (no changes)

    * All version parts allow leading zeroes (not allowed in spec)

Note: As indicated above, this is not strict Semver 2.0. Nuget advertises using Semver but is not strict in it's application
"""
#SERMVER_2_0_WITH_BUILD_PATTERN = r'^(?P<major>0|[1-9]\d*)(?:\.(?P<minor>0|[1-9]\d*))?(?:\.(?P<patch>0|[1-9]\d*))?(?:\.(?P<build>0|[1-9]\d*))?(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
SERMVER_2_0_WITH_BUILD_PATTERN = r'^(?P<major>[0-9]\d*)(?:\.(?P<minor>[0-9]\d*))?(?:\.(?P<patch>[0-9]\d*))?(?:\.(?P<build>[0-9]\d*))?(?:-(?P<prerelease>(?:[0-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
pattern = re.compile(SERMVER_2_0_WITH_BUILD_PATTERN)

class VersionPart(Enum):
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    BUILD = "build"
    PRERELEASE = "prerelease"
    BUILDMETADATA = "buildmetadata"

def is_full_release(version: str) -> bool:
    match = pattern.match(version)
    assert match, f':param version [{version}] is not a valid version.'
    return False if match.group(VersionPart.PRERELEASE.value) or \
        match.group(VersionPart.BUILDMETADATA.value) else True

def is_newer_release(version: str, compare: str) -> bool:
    v_match = pattern.match(version)
    assert v_match, f':param version [{version}] is not a valid version.'
    c_match = pattern.match(compare)
    assert c_match, f':param compare [{compare}] is not a valid version.'

    major = get_version_part(v_match, VersionPart.MAJOR)
    major_compare = get_version_part(c_match, VersionPart.MAJOR)
    if major_compare > major:
        return True
    if major_compare < major:
        return False

    minor = get_version_part(v_match, VersionPart.MINOR)
    minor_compare = get_version_part(c_match, VersionPart.MINOR)
    if minor_compare > minor:
        return True
    if minor_compare < minor:
        return False

    patch = get_version_part(v_match, VersionPart.PATCH)
    patch_compare = get_version_part(c_match, VersionPart.PATCH)
    if patch_compare > patch:
        return True
    if patch_compare < patch:
        return False

    build = get_version_part(v_match, VersionPart.BUILD)
    build_compare = get_version_part(c_match, VersionPart.BUILD)
    if build_compare > build:
        return True
    if build_compare < build:
        return False
    
    return False # Equal versions

def get_version_part(match: re.Match, version_part: VersionPart) -> int:
    """Returns the matched version part or the default value provided"""
    value = match.group(version_part.value)
    return int(value) if value else 0

def get_version_count_behind(version: str, compare: str) -> dict:
    """Returns a dict of VersionPart keys with the values set to count behind"""
    v_match = pattern.match(version)
    assert v_match, f':param version [{version}] is not a valid version.'
    c_match = pattern.match(compare)
    assert c_match, f':param compare [{compare}] is not a valid version.'

    result = {
        VersionPart.MAJOR: 0,
        VersionPart.MINOR: 0,
        VersionPart.PATCH: 0
    }

    result[VersionPart.MAJOR] = get_version_part_count_behind(v_match, c_match, VersionPart.MAJOR)
    if result[VersionPart.MAJOR] == 0:
        result[VersionPart.MINOR] = get_version_part_count_behind(v_match, c_match, VersionPart.MINOR)
        if result[VersionPart.MINOR] == 0:
            result[VersionPart.PATCH] = get_version_part_count_behind(v_match, c_match, VersionPart.PATCH)
            if result[VersionPart.PATCH] < 0:
                result[VersionPart.PATCH] = 0
    return result

def get_version_part_count_behind(match: re.Match, compare_match: re.match, version_part: VersionPart) -> int:
    """Returns the matched version part or the default value provided"""
    v = get_version_part(match, version_part)
    c = get_version_part(compare_match, version_part)    
    return c - v