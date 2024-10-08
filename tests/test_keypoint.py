import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pytest

import albumentations as A
import albumentations.augmentations.geometric.functional as fgeometric
from albumentations.core.keypoints_utils import (
    angle_to_2pi_range,
    convert_keypoint_from_albumentations,
    convert_keypoint_to_albumentations,
    convert_keypoints_from_albumentations,
    convert_keypoints_to_albumentations,
)
from albumentations.core.transforms_interface import BasicTransform
from albumentations.core.types import KeypointType


@pytest.mark.parametrize(
    ("kp", "source_format", "expected"),
    [
        ((20, 30), "xy", (20, 30, 0, 0)),
        (np.array([20, 30]), "xy", (20, 30, 0, 0)),
        ((20, 30), "yx", (30, 20, 0, 0)),
        ((20, 30, 60), "xys", (20, 30, 0, 60)),
        ((20, 30, 60), "xya", (20, 30, math.radians(60), 0)),
        ((20, 30, 60, 80), "xyas", (20, 30, math.radians(60), 80)),
    ],
)
def test_convert_keypoint_to_albumentations(kp: KeypointType, source_format: str, expected: KeypointType) -> None:
    image = np.ones((100, 100, 3))

    converted_keypoint = convert_keypoint_to_albumentations(
        kp, rows=image.shape[0], cols=image.shape[1], source_format=source_format
    )
    assert converted_keypoint == expected


@pytest.mark.parametrize(
    ["kp", "target_format", "expected"],
    [
        ((20, 30, 0, 0), "xy", (20, 30)),
        ((20, 30, 0, 0), "yx", (30, 20)),
        ((20, 30, 0.6, 0), "xya", (20, 30, math.degrees(0.6))),
        ((20, 30, 0, 0.6), "xys", (20, 30, 0.6)),
        ((20, 30, 0.6, 80), "xyas", (20, 30, math.degrees(0.6), 80)),
    ],
)
def test_convert_keypoint_from_albumentations(kp: KeypointType, target_format: str, expected: KeypointType) -> None:
    image = np.ones((100, 100, 3))
    converted_keypoint = convert_keypoint_from_albumentations(
        kp, rows=image.shape[0], cols=image.shape[1], target_format=target_format
    )
    assert converted_keypoint == expected


@pytest.mark.parametrize(
    ["kp", "keypoint_format"],
    [
        ((20, 30, 40, 50), "xy"),
        ((20, 30, 40, 50, 99), "xyas"),
        ((20, 30, 60, 80), "xysa"),
        ((20, 30, 60, 80, 99), "yx"),
    ],
)
def test_convert_keypoint_to_albumentations_and_back(kp: KeypointType, keypoint_format: str) -> None:
    image = np.ones((100, 100, 3))
    converted_kp = convert_keypoint_to_albumentations(
        kp, rows=image.shape[0], cols=image.shape[1], source_format=keypoint_format
    )
    converted_back_kp = convert_keypoint_from_albumentations(
        converted_kp,
        rows=image.shape[0],
        cols=image.shape[1],
        target_format=keypoint_format,
    )
    assert converted_back_kp == kp


def test_convert_keypoints_to_albumentations() -> None:
    keypoints = [(20, 30, 40, 50), (30, 40, 50, 60, 99)]
    image = np.ones((100, 100, 3))
    converted_keypoints = convert_keypoints_to_albumentations(
        keypoints, rows=image.shape[0], cols=image.shape[1], source_format="xyas"
    )
    converted_keypoint_1 = convert_keypoint_to_albumentations(
        keypoints[0], rows=image.shape[0], cols=image.shape[1], source_format="xyas"
    )
    converted_keypoint_2 = convert_keypoint_to_albumentations(
        keypoints[1], rows=image.shape[0], cols=image.shape[1], source_format="xyas"
    )
    assert converted_keypoints == [converted_keypoint_1, converted_keypoint_2]


def test_convert_keypoints_from_albumentations() -> None:
    keypoints = [(0.2, 0.3, 0.6, 0.8), (0.3, 0.4, 0.7, 0.9, 99)]
    image = np.ones((100, 100, 3))
    converted_keypoints = convert_keypoints_from_albumentations(
        keypoints, rows=image.shape[0], cols=image.shape[1], target_format="xyas"
    )
    converted_keypoint_1 = convert_keypoint_from_albumentations(
        keypoints[0], rows=image.shape[0], cols=image.shape[1], target_format="xyas"
    )
    converted_keypoint_2 = convert_keypoint_from_albumentations(
        keypoints[1], rows=image.shape[0], cols=image.shape[1], target_format="xyas"
    )
    assert converted_keypoints == [converted_keypoint_1, converted_keypoint_2]


@pytest.mark.parametrize(
    ["keypoints", "keypoint_format", "labels"],
    [
        ([(20, 30, 40, 50)], "xyas", [1]),
        ([(20, 30, 40, 50, 99), (10, 40, 30, 20, 9)], "xy", None),
        ([(20, 30, 60, 80)], "yx", [2]),
        ([(20, 30, 60, 80, 99)], "xys", None),
    ],
)
def test_compose_with_keypoint_noop(keypoints: KeypointType, keypoint_format: str, labels: Optional[List[int]]) -> None:
    image = np.ones((100, 100, 3))
    if labels is not None:
        aug = A.Compose(
            [A.NoOp(p=1.0)],
            keypoint_params={"format": keypoint_format, "label_fields": ["labels"]},
        )
        transformed = aug(image=image, keypoints=keypoints, labels=labels)
    else:
        aug = A.Compose([A.NoOp(p=1.0)], keypoint_params={"format": keypoint_format})
        transformed = aug(image=image, keypoints=keypoints)
    assert np.array_equal(transformed["image"], image)
    assert transformed["keypoints"] == keypoints


@pytest.mark.parametrize(
    ["keypoints", "keypoint_format"], [[[[20, 30, 40, 50]], "xyas"]]
)
def test_compose_with_keypoint_noop_error_label_fields(keypoints: KeypointType, keypoint_format: str) -> None:
    image = np.ones((100, 100, 3))
    aug = A.Compose(
        [A.NoOp(p=1.0)],
        keypoint_params={"format": keypoint_format, "label_fields": "class_id"},
    )
    with pytest.raises(Exception):
        aug(image=image, keypoints=keypoints, cls_id=[0])


@pytest.mark.parametrize(
    ["keypoints", "keypoint_format", "labels"],
    [
        ([(20, 30, 60, 80)], "xy", {"label": [1]}),
        ([], "xy", {}),
        ([], "xy", {"label": []}),
        ([(20, 30, 60, 80)], "xy", {"id": [3]}),
        ([(20, 30, 60, 80), (30, 40, 40, 50)], "xy", {"id": [3, 1]}),
    ],
)
def test_compose_with_keypoint_noop_label_outside(keypoints: KeypointType, keypoint_format: str, labels: Dict[str, Any]) -> None:
    image = np.ones((100, 100, 3))
    aug = A.Compose(
        [A.NoOp(p=1.0)],
        keypoint_params={
            "format": keypoint_format,
            "label_fields": list(labels.keys()),
        },
    )
    transformed = aug(image=image, keypoints=keypoints, **labels)
    assert np.array_equal(transformed["image"], image)
    assert transformed["keypoints"] == keypoints
    for k, v in labels.items():
        assert transformed[k] == v


def test_random_sized_crop_size() -> None:
    image = np.ones((100, 100, 3))
    keypoints = [(0.2, 0.3, 0.6, 0.8), (0.3, 0.4, 0.7, 0.9, 99)]
    aug = A.RandomSizedCrop(min_max_height=(70, 90), size=(50, 50), p=1.0)
    transformed = aug(image=image, keypoints=keypoints)
    assert transformed["image"].shape == (50, 50, 3)
    assert len(keypoints) == len(transformed["keypoints"])


def test_random_resized_crop_size() -> None:
    image = np.ones((100, 100, 3))
    keypoints = [(0.2, 0.3, 0.6, 0.8), (0.3, 0.4, 0.7, 0.9, 99)]
    aug = A.RandomResizedCrop(size=(50, 50), p=1.0)
    transformed = aug(image=image, keypoints=keypoints)
    assert transformed["image"].shape == (50, 50, 3)
    assert len(keypoints) == len(transformed["keypoints"])


@pytest.mark.parametrize(
    ["aug", "keypoints", "expected"],
    [
        [A.HorizontalFlip, [[0, 0]], [[2, 0]]],
        [A.HorizontalFlip, [[2, 0]], [[0, 0]]],
        [A.HorizontalFlip, [[0, 2]], [[2, 2]]],
        [A.HorizontalFlip, [[2, 2]], [[0, 2]]],
        #
        [A.VerticalFlip, [[0, 0]], [[0, 2]]],
        [A.VerticalFlip, [[2, 0]], [[2, 2]]],
        [A.VerticalFlip, [[0, 2]], [[0, 0]]],
        [A.VerticalFlip, [[2, 2]], [[2, 0]]],
        #
        [A.HorizontalFlip, [[1, 1]], [[1, 1]]],
        [A.VerticalFlip, [[1, 1]], [[1, 1]]],
    ],
)
def test_keypoint_flips_transform_3x3(aug: BasicTransform, keypoints: KeypointType, expected: KeypointType) -> None:
    transform = A.Compose([aug(p=1)], keypoint_params={"format": "xy"})

    image = np.ones((3, 3, 3))
    transformed = transform(
        image=image, keypoints=keypoints, labels=np.ones(len(keypoints))
    )
    assert np.allclose(expected, transformed["keypoints"])


@pytest.mark.parametrize(
    ["aug", "keypoints", "expected"],
    [
        [A.HorizontalFlip, [[20, 30, 0, 0]], [[79, 30, 180, 0]]],
        [A.HorizontalFlip, [[20, 30, 45, 0]], [[79, 30, 135, 0]]],
        [A.HorizontalFlip, [[20, 30, 90, 0]], [[79, 30, 90, 0]]],
        [A.VerticalFlip, [[20, 30, 0, 0]], [[20, 69, 0, 0]]],
        [A.VerticalFlip, [[20, 30, 45, 0]], [[20, 69, 315, 0]]],
        [A.VerticalFlip, [[20, 30, 90, 0]], [[20, 69, 270, 0]]],
    ],
)
def test_keypoint_transform_format_xyas(aug: BasicTransform, keypoints: KeypointType, expected: KeypointType) -> None:
    transform = A.Compose(
        [aug(p=1)],
        keypoint_params={
            "format": "xyas",
            "angle_in_degrees": True,
            "label_fields": ["labels"],
        },
    )

    image = np.ones((100, 100, 3))
    transformed = transform(
        image=image, keypoints=keypoints, labels=np.ones(len(keypoints))
    )
    assert np.allclose(expected, transformed["keypoints"])


@pytest.mark.parametrize(
    ["keypoint", "expected", "factor"],
    [
        ((20, 30, math.pi / 2, 0), (20, 30, math.pi / 2, 0), 0),
        ((20, 30, math.pi / 2, 0), (30, 179, 0, 0), 1),
        ((20, 30, math.pi / 2, 0), (179, 69, 3 * math.pi / 2, 0), 2),
        ((20, 30, math.pi / 2, 0), (69, 20, math.pi, 0), 3),
    ],
)
def test_keypoint_rotate90(keypoint: KeypointType, expected: KeypointType, factor: int) -> None:
    actual = fgeometric.keypoint_rot90(keypoint, factor, rows=100, cols=200)
    assert actual == expected


@pytest.mark.parametrize(
    ["keypoint", "expected", "angle"],
    [
        [[20, 30, math.pi / 2, 0], [20, 30, math.pi / 2, 0], 0],
        [[20, 30, math.pi / 2, 0], [30, 79, math.pi, 0], 90],
        [[20, 30, math.pi / 2, 0], [79, 69, 3 * math.pi / 2, 0], 180],
        [[20, 30, math.pi / 2, 0], [69, 20, 0, 0], 270],
        [[0, 0, 0, 0], [99, 99, math.pi, 0], 180],
        [[99, 99, 0, 0], [0, 0, math.pi, 0], 180],
    ],
)
def test_keypoint_rotate(keypoint: KeypointType, expected: KeypointType, angle: float) -> None:
    actual = fgeometric.keypoint_rotate(keypoint, angle, rows=100, cols=100)
    np.testing.assert_allclose(actual, expected, atol=1e-7)


@pytest.mark.parametrize(
    ["keypoint", "expected", "scale"],
    [
        [[0.0, 0.0, math.pi / 2, 1], [0.0, 0.0, math.pi / 2, 1], 1],
        [[0.0, 0.0, math.pi / 2, 1], [0.0, 0.0, math.pi / 2, 2], 2],
        [[0.0, 0.0, math.pi / 2, 1], [0.0, 0.0, math.pi / 2, 0.5], 0.5],
    ],
)
def test_keypoint_scale(keypoint: KeypointType, expected: KeypointType, scale: float) -> None:
    actual = fgeometric.keypoint_scale(keypoint, scale, scale)
    np.testing.assert_allclose(actual, expected, atol=1e-7)


def test_compose_with_additional_targets() -> None:
    image = np.ones((100, 100, 3))
    keypoints = [(10, 10), (50, 50)]
    kp1 = [(15, 15), (55, 55)]

    aug = A.Compose(
        [A.CenterCrop(50, 50)],
        keypoint_params={"format": "xy"},
        additional_targets={"kp1": "keypoints"},
    )
    transformed = aug(image=image, keypoints=keypoints, kp1=kp1)
    assert transformed["keypoints"] == [(25, 25)]
    assert transformed["kp1"] == [(30, 30)]

    aug = A.Compose([A.CenterCrop(50, 50)], keypoint_params={"format": "xy"})
    aug.add_targets(additional_targets={"kp1": "keypoints"})
    transformed = aug(image=image, keypoints=keypoints, kp1=kp1)
    assert transformed["keypoints"] == [(25, 25)]
    assert transformed["kp1"] == [(30, 30)]


@pytest.mark.parametrize(
    ["angle", "expected"],
    [
        [0, 0],
        [np.pi / 2, np.pi / 2],
        [np.pi, np.pi],
        [3 * np.pi / 2, 3 * np.pi / 2],
        [2 * np.pi, 0],
        [-np.pi / 2, 3 * np.pi / 2],
        [-np.pi, np.pi],
        [-3 * np.pi / 2, np.pi / 2],
        [-2 * np.pi, 0],
    ],
)
def test_angle_to_2pi_range(angle, expected) -> None:
    assert np.isclose(angle_to_2pi_range(angle), expected)


def test_coarse_dropout() -> None:
    aug = A.Compose(
        [
            A.CoarseDropout(
                min_holes=1,
                max_holes=1,
                min_height=128,
                max_width=128,
                min_width=128,
                max_height=128,
                p=1,
            )
        ],
        keypoint_params=A.KeypointParams(format="xy"),
    )

    result = aug(image=np.zeros((128, 128)), keypoints=((10, 10), (20, 30)))
    assert len(result["keypoints"]) == 0


@pytest.mark.parametrize(
    ["keypoints", "expected_keypoints", "holes"],
    [
        [
            [(50, 50, 0, 0), (75, 75, 0, 0)],
            [],
            [(40, 40, 60, 60), (70, 70, 80, 80), (10, 10, 20, 20)],
        ],
        [
            [(50, 50, 0, 0), (75, 75, 0, 0)],
            [],
            [(10, 10, 20, 20), (40, 40, 60, 60), (70, 70, 80, 80)],
        ],
        [
            [(50, 50, 0, 0), (75, 75, 0, 0)],
            [],
            [(40, 40, 60, 60), (10, 10, 20, 20), (70, 70, 80, 80)],
        ],
        [
            [(50, 50, 0, 0), (75, 75, 0, 0)],
            [(75, 75, 0, 0)],
            [(40, 40, 60, 60), (10, 10, 20, 20)],
        ],
        [
            [(50, 50, 0, 0), (75, 75, 0, 0)],
            [(50, 50, 0, 0)],
            [(70, 70, 80, 80), (10, 10, 20, 20)],
        ],
        [
            [(50, 50, 0, 0), (75, 75, 0, 0)],
            [(50, 50, 0, 0), (75, 75, 0, 0)],
            [(10, 10, 20, 20)],
        ],
    ],
)
def test_coarse_dropout_remove_keypoints(
    keypoints: KeypointType,
    expected_keypoints: KeypointType,
    holes: List[Tuple[int, int, int, int]],
) -> None:
    t = A.CoarseDropout()
    result_keypoints = t.apply_to_keypoints(keypoints, holes)

    assert set(result_keypoints) == set(expected_keypoints)



@pytest.mark.parametrize("keypoints, image_shape, expected", [
    (
        np.array([[0, 0], [50, 50], [100, 100], [-10, 50], [50, -10], [110, 50], [50, 110]]),
        (100, 100),
        np.array([[0, 0], [50, 50]])
    ),
    (
        np.array([[0, 0, 0], [50, 50, 90], [100, 100, 180], [-10, 50, 45], [50, -10, 135], [110, 50, 270], [50, 110, 315]]),
        (100, 100),
        np.array([[0, 0, 0], [50, 50, 90]])
    ),
    (
        np.array([[10, 10], [20, 20]]),
        (30, 30),
        np.array([[10, 10], [20, 20]])
    ),
])
def test_validate_keypoints(keypoints, image_shape, expected):
    result = fgeometric.validate_keypoints(keypoints, image_shape)
    np.testing.assert_array_almost_equal(result, expected)

def test_validate_keypoints_all_invalid():
    keypoints = np.array([[-1, -1], [101, 101]])
    result = fgeometric.validate_keypoints(keypoints, (100, 100))
    assert result.shape == (0, 2)
