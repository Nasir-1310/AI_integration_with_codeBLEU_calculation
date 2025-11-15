class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        seen_numbers = {}
        for i, num in enumerate(nums):
            complement = target - num
            if complement in seen_numbers:
                return [seen_numbers[complement], i]
            seen_numbers[num] = i
        return [] # Should not be reached based on problem constraints (exactly one solution)