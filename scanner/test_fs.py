from filesystem import measure_path_size

if __name__ == "__main__":
    size, notes = measure_path_size("test_dir")
    print("SIZE:", size)
    print("NOTES:")
    for n in notes:
        print("-", n)
