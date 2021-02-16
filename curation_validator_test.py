import unittest
from unittest.mock import patch

from curation_validator import validate_curation


def mock_get_tag_list() -> list[str]:
    return ["A", "B"]


class TestCurationValidator(unittest.TestCase):

    def setUp(self):
        self.patcher = patch('curation_validator.get_tag_list')
        self.tag_list = self.patcher.start()
        self.tag_list.side_effect = mock_get_tag_list

    def tearDown(self):
        self.patcher.stop()

    def test_valid_yaml_meta(self):
        for extension in ["7z", "zip"]:
            errors, warnings, is_extreme = validate_curation(f"test_curations/test_curation_valid.{extension}")
            self.assertCountEqual(errors, [])
            self.assertCountEqual(warnings, [])
            self.assertFalse(is_extreme)

    def test_valid_yaml_meta_extreme(self):
        for extension in ["7z", "zip"]:
            errors, warnings, is_extreme = validate_curation(f"test_curations/test_curation_valid_extreme.{extension}")
            self.assertCountEqual(errors, [])
            self.assertCountEqual(warnings, [])
            self.assertTrue(is_extreme)

    def test_valid_legacy(self):
        for extension in ["7z", "zip"]:
            errors, warnings, is_extreme = validate_curation(f"test_curations/test_curation_valid_legacy.{extension}")
            self.assertCountEqual(errors, [])
            self.assertCountEqual(warnings, [])
            self.assertFalse(is_extreme)

    def test_curation_invalid_archive(self):
        for extension in ["7z", "zip"]:
            errors, warnings, is_extreme = validate_curation(f"test_curations/test_curation_invalid_archive.{extension}")
            self.assertCountEqual(errors, [f"There seems to a problem with your {extension} file."])
            self.assertCountEqual(warnings, [])

    def test_curation_too_large(self):
        for extension in ["7z", "zip"]:
            errors, warnings, _ = validate_curation(f"test_curations/test_curation_2GB.{extension}")
            self.assertCountEqual(errors, [])
            self.assertCountEqual(warnings, ["The archive is too large to validate (`2000MB/1000MB`)."])

    def test_empty_content(self):
        for extension in ["7z", "zip"]:
            errors, warnings, _ = validate_curation(f"test_curations/test_curation_empty_content.{extension}")
            self.assertCountEqual(errors, ["No files found in content folder."])
            self.assertCountEqual(warnings, [])

    def test_missing_content(self):
        for extension in ["7z", "zip"]:
            errors, warnings, _ = validate_curation(f"test_curations/test_curation_missing_content.{extension}")
            self.assertCountEqual(errors, ["Content folder not found."])
            self.assertCountEqual(warnings, [])

    def test_missing_logo(self):
        for extension in ["7z", "zip"]:
            errors, warnings, _ = validate_curation(f"test_curations/test_curation_missing_logo.{extension}")
            self.assertCountEqual(errors, ["Logo file is either missing or its filename is incorrect."])
            self.assertCountEqual(warnings, [])

    def test_missing_meta(self):
        for extension in ["7z", "zip"]:
            errors, warnings, _ = validate_curation(f"test_curations/test_curation_missing_meta.{extension}")
            self.assertCountEqual(errors,
                                  ["Meta file is either missing or its filename is incorrect. Are you using Flashpoint Core for curating?"])
            self.assertCountEqual(warnings, [])

    def test_missing_root_folder(self):
        for extension in ["7z", "zip"]:
            errors, warnings, _ = validate_curation(f"test_curations/test_curation_missing_root_folder.{extension}")
            self.assertCountEqual(errors, ["Logo, screenshot, content folder and meta not found. Is your curation structured properly?"])
            self.assertCountEqual(warnings, [])

    # def test_missing_root_folder(self):
    #     for extension in ["7z", "zip"]:
    #         errors, warnings, _ = validate_curation(f"test_curations/test_curation_missing_root_folder.{extension}")
    #         self.assertCountEqual(errors, ["Found meta file outside root directory. Did you forgot to enclose the files into one directory?"])
    #         self.assertCountEqual(warnings, [])

    def test_missing_ss(self):
        for extension in ["7z", "zip"]:
            errors, warnings, _ = validate_curation(f"test_curations/test_curation_missing_ss.{extension}")
            self.assertCountEqual(errors, ["Screenshot file is either missing or its filename is incorrect."])
            self.assertCountEqual(warnings, [])

    def test_unknown_tag_warning(self):
        for extension in ["7z", "zip"]:
            errors, warnings, _ = validate_curation(f"test_curations/test_curation_unknown_tag.{extension}")
            self.assertCountEqual(errors, [])
            self.assertCountEqual(warnings,
                                  ["Tag `Unknown Tag` is not a known tag (did you write it correctly?). Ignore if you're adding a new tag.",
                                   "Tag `Another Unknown Tag` is not a known tag (did you write it correctly?). Ignore if you're adding a new tag."])

    def test_missing_tags(self):
        for extension in ["7z", "zip"]:
            errors, warnings, _ = validate_curation(f"test_curations/test_curation_missing_tags.{extension}")
            self.assertCountEqual(errors, ["Missing tags. At least one tag must be specified."])
            self.assertCountEqual(warnings, [])

    def test_missing_title(self):
        for extension in ["7z", "zip"]:
            errors, warnings, _ = validate_curation(f"test_curations/test_curation_missing_title.{extension}")
            self.assertCountEqual(errors, ["The `Title` property in the meta file is mandatory."])
            self.assertCountEqual(warnings, [])

    def test_missing_application_path_warning(self):
        for extension in ["7z", "zip"]:
            errors, warnings, _ = validate_curation(f"test_curations/test_curation_missing_application_path.{extension}")
            self.assertCountEqual(errors, ["The `Application Path` property in the meta file is mandatory."])
            self.assertCountEqual(warnings, [])

    def test_missing_launch_command(self):
        for extension in ["7z", "zip"]:
            errors, warnings, _ = validate_curation(f"test_curations/test_curation_missing_launch_command.{extension}")
            self.assertCountEqual(errors, ["The `Launch Command` property in the meta file is mandatory."])
            self.assertCountEqual(warnings, [])

    def test_missing_lanugages(self):
        for extension in ["7z", "zip"]:
            errors, warnings, _ = validate_curation(f"test_curations/test_curation_missing_lanugages.{extension}")
            self.assertCountEqual(errors, ["The `Languages` property in the meta file is mandatory."])
            self.assertCountEqual(warnings, [])

    def test_missing_status(self):
        for extension in ["7z", "zip"]:
            errors, warnings, _ = validate_curation(f"test_curations/test_curation_missing_status.{extension}")
            self.assertCountEqual(errors, ["The `Status` property in the meta file is mandatory."])
            self.assertCountEqual(warnings, [])


if __name__ == '__main__':
    unittest.main()