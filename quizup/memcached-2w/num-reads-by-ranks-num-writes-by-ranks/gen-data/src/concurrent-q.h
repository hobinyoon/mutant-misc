#pragma once

#include <queue>
#include <mutex>


class ConQEmpty {
};


template <typename T>
class ConcurrentQ {
private:
	std::queue<T> _q;
	std::mutex _mutex;

public:
	ConcurrentQ() {
	}

	virtual ~ConcurrentQ() {
	}

	T Pop() {
		std::lock_guard<std::mutex> lock(_mutex);
		if (_q.empty())
			throw ConQEmpty();
		T e = _q.front();
		_q.pop();
		return e;
	}

	void Push(const T& e) {
		std::lock_guard<std::mutex> lock(_mutex);
		_q.push(e);
	}
};
