for img in $(docker images -q); do
    parent=$(docker inspect --format='{{.Parent}}' $img 2>/dev/null)
    if [ "$parent" = "aacd11aa4d7f" ]; then
        echo "Child image: $img"
    fi
done
