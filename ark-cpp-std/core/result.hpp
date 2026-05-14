#ifndef ARK_CPP_STD_CORE_RESULT_HPP
#define ARK_CPP_STD_CORE_RESULT_HPP

#include <variant>
#include <string>
#include <stdexcept>
#include <utility>

namespace ark {

// Helper type for errors
template <typename E>
struct ErrImpl {
    E error;
};

template <typename E>
ErrImpl<E> Err(E error) {
    return ErrImpl<E>{std::move(error)};
}

// Result class mimicking Rust's Result
template <typename T, typename E = std::string>
class Result {
    std::variant<T, E> data_;
    bool is_ok_;

public:
    Result(T val) : data_(std::move(val)), is_ok_(true) {}
    Result(ErrImpl<E> err) : data_(std::move(err.error)), is_ok_(false) {}

    bool is_ok() const { return is_ok_; }
    bool is_err() const { return !is_ok_; }

    T unwrap() {
        if (is_ok_) {
            return std::move(std::get<T>(data_));
        } else {
            throw std::runtime_error("Called unwrap on an Err value");
        }
    }

    T or_throw() {
        if (is_ok_) {
            return std::move(std::get<T>(data_));
        } else {
            // Simplified error throwing.
            // If E is a string, we throw it, otherwise a generic error.
            if constexpr (std::is_same_v<E, std::string>) {
                throw std::runtime_error(std::get<E>(data_));
            } else {
                throw std::runtime_error("Result error");
            }
        }
    }

    E unwrap_err() {
        if (!is_ok_) {
            return std::move(std::get<E>(data_));
        } else {
            throw std::runtime_error("Called unwrap_err on an Ok value");
        }
    }
};

} // namespace ark

#endif // ARK_CPP_STD_CORE_RESULT_HPP
